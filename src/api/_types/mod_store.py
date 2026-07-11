"""Shared, deduplicated mod store.

Each mod+version zip is downloaded once into a single store and *hardlinked* into
every server that uses it, instead of being copied per server. Because a given
mod+version zip is immutable, the bytes are safe to share, and the inode link
count (``st_nlink``) gives free reference counting: a server that links a store
file is the "lock" keeping it alive, and the store file is only reclaimed once no
server references it.

Hardlinks require the store and the server's mods directory to live on one
filesystem. Both backends satisfy this, they just place the files differently:

* **Docker** bind-mounts the host ``server_directory`` at ``/factorio``, so the
  store (``MOD_STORE_DIRECTORY``) and ``server_directory/mods`` share the host
  filesystem. The container sees the hardlink as a normal file.
* **Kubernetes** keeps both the store and every server's mods directory inside a
  single ``ReadWriteMany`` volume (``MOD_SHARED_ROOT``). Each Factorio pod mounts
  its per-server mods directory (a ``subPath`` of that volume) at
  ``/factorio/mods``; hardlinks survive the ``subPath`` mount because they are
  inode entries, not path references into the store.

When a hardlink cannot be created (e.g. a cross-device ``EXDEV`` error or a
filesystem without hardlink support) we fall back to a byte copy, which stays
correct but forgoes deduplication for that server.
"""

from __future__ import annotations

import contextlib
import logging
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from api._types.enums import BackendKind
from api.constants import MOD_STORE_DIRECTORY, AppConfig

if TYPE_CHECKING:
    from api._types.server.core import Server

logger = logging.getLogger(__name__)


def _backend() -> BackendKind:
    return BackendKind(AppConfig.SERVER_BACKEND.lower())


def _shared_root() -> Path:
    return Path(AppConfig.MOD_SHARED_ROOT)


def store_root() -> Path:
    """Directory holding exactly one copy of each mod+version zip."""
    if _backend() is BackendKind.KUBERNETES:
        return _shared_root() / "store"
    return MOD_STORE_DIRECTORY


def _safe_component(value: str, *, field: str) -> str:
    """Return ``value`` if it is a single, safe path component, else raise.

    Rejects path separators, parent references and NULs so an attacker-influenced
    mod or file name can never escape the store root via traversal.
    """
    if not value or value in {".", ".."} or "/" in value or "\\" in value or "\x00" in value:
        msg = f"Unsafe {field}: {value!r}"
        raise ValueError(msg)
    return value


def store_path(mod_name: str, file_name: str) -> Path:
    """Absolute path of the single stored copy for ``{mod}_{version}.zip``."""
    root = store_root()
    candidate = (root / _safe_component(mod_name, field="mod name") / _safe_component(file_name, field="file name"))
    # Defence in depth: ensure the resolved path stays within the store root.
    if not candidate.resolve().is_relative_to(root.resolve()):
        msg = f"Resolved mod path escapes the store root: {candidate}"
        raise ValueError(msg)
    return candidate


def is_stored(mod_name: str, file_name: str) -> bool:
    return store_path(mod_name, file_name).exists()


def server_mods_dir(server: Server) -> Path:
    """Directory holding this server's hardlinks into the store.

    Docker uses the host ``server_directory/mods`` (bind-mounted into the pod).
    Kubernetes uses a per-server directory inside the shared volume so it shares
    a filesystem with the store and is mounted into the pod at ``/factorio/mods``.
    """
    if _backend() is BackendKind.KUBERNETES:
        return _shared_root() / "servers" / f"{server.user.id}" / server.name / "mods"
    return server.files.directory / "mods"


def link_into(store_file: Path, destination: Path) -> None:
    """Hardlink a stored archive into a server's mods directory.

    Replaces any existing destination (re-install / stale link). Falls back to a
    byte copy (with a logged warning) when the link cannot be created.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        destination.unlink(missing_ok=True)
    try:
        os.link(store_file, destination)
    except FileExistsError:
        # Concurrent linker won the race; the file is present, treat as success.
        pass
    except OSError as exc:
        logger.warning(
            "Hardlink %s -> %s failed (%s); copying instead.",
            store_file,
            destination,
            exc,
        )
        shutil.copy2(store_file, destination)


def is_referenced(mod_name: str, file_name: str) -> bool:
    """Whether any server still links the given store file.

    The inode link count is authoritative: ``> 1`` means at least one server's
    mods directory links it besides the store copy itself.
    """
    store_file = store_path(mod_name, file_name)
    if not store_file.exists():
        return False
    return store_file.stat().st_nlink > 1


def gc_if_unreferenced(mod_name: str, file_name: str) -> bool:
    """Delete the store file when no server references it. Returns True if removed."""
    store_file = store_path(mod_name, file_name)
    try:
        if not store_file.exists() or is_referenced(mod_name, file_name):
            return False
        store_file.unlink(missing_ok=True)
        with contextlib.suppress(OSError):
            store_file.parent.rmdir()  # prune now-empty {mod}/ dir
    except OSError as exc:
        logger.warning("Store GC failed for %s: %s", store_file, exc)
        return False
    return True
