import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from api._types.dicts import ServerModEntry
from api._types.server.core import Server

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable
    from pathlib import Path

    from api._types.server.files import ServerFiles



@dataclass
class ModDescription:
    name: str
    enabled: bool
    version: str | None
    archives: list[ModArchive]
    has_archive: bool
    is_core: bool
    playable: bool

@dataclass
class ModArchive:
    version: str
    filename: str
    size_bytes: int
    size_label: str

class ServerMods:
    """Mod-list and mod-archive operations, namespaced under ``server.mods``.

    Reads/writes the server's mods directory and mods-list.json (via server.files)
    and reconciles them against the bundled DLC the game reports in its startup log.
    """

    # Factorio logs every mod it loads at startup, e.g.
    #   "   0.107 Loading mod base 2.0.20 (data.lua)".
    _LOADING_MOD_RE = re.compile(r"Loading mod (\S+) ([\d.]+)")

    def __init__(self: Self, server: Server) -> None:
        self._server = server

    @property
    def _files(self: Self) -> ServerFiles:
        return self._server.files

    def ensure_workspace(self: Self) -> None:
        self._files.mods_dir.mkdir(parents=True, exist_ok=True)
        if not self._files.mods_list.exists():
            default = {"mods": [{"name": "base", "enabled": True}]}
            with self._files.mods_list.open("w") as f:
                json.dump(default, f, indent=2)

    def read_list(self: Self) -> list[ServerModEntry]:
        self.ensure_workspace()
        with self._files.mods_list.open() as f:
            payload = json.load(f)
        raw: list[dict[str, Any]] = payload.get("mods", [])
        mods = [
            ServerModEntry(
                name=str(entry["name"]),
                enabled=bool(entry.get("enabled", True)),
                version=entry.get("version"),
            )
            for entry in raw
            if entry.get("name")
        ]
        if not any(mod.name == "base" for mod in mods):
            mods.insert(0, ServerModEntry(name="base", enabled=True))
            self.write_list(mods)
        return mods

    def write_list(self: Self, mods: Iterable[ServerModEntry]) -> None:
        """Write the given list of mods to the mods-list.json file."""
        self.ensure_workspace()
        normalized: list[ServerModEntry] = list(mods)
        if not any(mod.name == "base" for mod in normalized):
            normalized.insert(0, ServerModEntry(name="base", enabled=True))
        serializable = [
            {"name": mod.name, "enabled": mod.enabled}
            | ({"version": mod.version} if mod.version else {})
            for mod in normalized
        ]
        with self._files.mods_list.open("w") as f:
            json.dump({"mods": serializable}, f, indent=2)

    def upsert(self: Self, name: str, *, enabled: bool, version: str | None = None) -> None:
        mods = self.read_list()
        for mod in mods:
            if mod.name == name:
                mod.enabled = enabled
                if version:
                    mod.version = version
                else:
                    mod.version = None
                break
        else:
            entry = ServerModEntry(name=name, enabled=enabled)
            if version:
                entry.version = version
            mods.append(entry)
        self.write_list(mods)

    def remove_entry(self: Self, name: str) -> None:
        mods = [mod for mod in self.read_list() if mod.name != name]
        self.write_list(mods)

    def link_from_store(self: Self, mod_name: str, file_name: str) -> Path:
        """Link an already-stored archive into this server's mods directory.

        The caller ensures the store file exists (downloaded once). Returns the
        link destination inside the server's mods directory.
        """
        from api._types import mod_store  # noqa: PLC0415

        self.ensure_workspace()
        destination = self._files.mods_dir / file_name
        mod_store.link_into(mod_store.store_path(mod_name, file_name), destination)
        return destination

    def remove_archives(self: Self, name: str, *, gc_store: bool = True) -> None:
        if not self._files.mods_dir.exists():
            return
        from api._types import mod_store  # noqa: PLC0415

        for archive in self._files.mods_dir.glob(f"{name}_*.zip"):
            file_name = archive.name
            # Unlink this server's link first so the store refcount has already
            # dropped when GC inspects it.
            archive.unlink(missing_ok=True)
            if gc_store:
                parsed = self._split_archive_name(file_name)
                if parsed:
                    mod_store.gc_if_unreferenced(parsed[0], file_name)

    def _discover_archives(self: Self) -> dict[str, list[ModArchive]]:
        if not self._files.mods_dir.exists():
            return {}

        archives: dict[str, list[ModArchive]] = {}
        for archive in self._files.mods_dir.glob("*.zip"):
            parsed = self._split_archive_name(archive.name)
            if not parsed:
                continue
            mod_name, version = parsed
            size_bytes = archive.stat().st_size
            archives.setdefault(mod_name, []).append(
                ModArchive(
                    version=version,
                    filename=archive.name,
                    size_bytes=size_bytes,
                    size_label=f"{size_bytes / 1048576:.1f} MB",
                ),
            )
        return archives

    @staticmethod
    def _split_archive_name(filename: str) -> tuple[str, str] | None:
        if not filename.endswith(".zip"):
            return None
        stem = filename[:-4]
        if "_" not in stem:
            return None
        name, version = stem.rsplit("_", 1)
        return name, version

    @staticmethod
    def _version_key(version: str) -> tuple[int, ...]:
        parts: list[int] = []
        for part in version.split("."):
            if part.isdigit():
                parts.append(int(part))
            else:
                parts.append(0)
        return tuple(parts)

    def discover_playable_mods(self: Self) -> dict[str, str]:
        """Discover the mods the game itself reports loading, from its log.

        Parses the current (then previous) Factorio log for ``Loading mod`` lines
        and returns a ``{name: version}`` map of everything the game considers
        playable -- including the bundled DLC (``space-age``, ``quality``,
        ``elevated-rails`` ...) that ship inside the game image with no archive.
        The engine-internal ``core`` pseudo-mod is excluded. Returns an empty map
        if the server has never started (no log yet).
        """
        for log_file in (self._files.current_log, self._files.previous_log):
            discovered = self._parse_loaded_mods(log_file)
            if discovered:
                return discovered
        return {}

    def _parse_loaded_mods(self: Self, log_file: Path) -> dict[str, str]:
        if not log_file.exists():
            return {}
        discovered: dict[str, str] = {}
        with log_file.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                match = self._LOADING_MOD_RE.search(line)
                if match:
                    name, version = match.group(1), match.group(2)
                    if name != "core":
                        discovered[name] = version
                elif discovered and "Checksum of" in line:
                    # Mods are loaded in one contiguous startup block; stop once
                    # the game moves on so we never scan a multi-MB log fully.
                    break
        return discovered

    def bundled(self: Self) -> dict[str, str]:
        """Playable mods that ship with the game (no downloadable archive).

        These are the discovered mods with no zip in the mods directory. ``base``
        is always treated as bundled even before the first launch.
        """
        archives = self._discover_archives()
        bundled = {
            name: version
            for name, version in self.discover_playable_mods().items()
            if name not in archives
        }
        bundled.setdefault("base", bundled.get("base", ""))
        return bundled

    def is_bundled(self: Self, name: str) -> bool:
        """Whether a mod ships with the game and so cannot be removed."""
        return name == "base" or name in self.bundled()

    def describe(self: Self) -> list[ModDescription]:
        entries = self.read_list()
        archives = self._discover_archives()
        bundled = self.bundled()
        described: list[ModDescription] = []
        listed: set[str] = set()
        for entry in entries:
            mod_archives = archives.get(entry.name, [])
            mod_archives.sort(key=lambda item: self._version_key(item.version), reverse=True)
            has_archive = bool(mod_archives)
            is_core = entry.name == "base" or (entry.name in bundled and not has_archive)
            resolved_version = entry.version
            if not resolved_version and mod_archives:
                resolved_version = mod_archives[0].version
            if not resolved_version and entry.name in bundled:
                resolved_version = bundled[entry.name] or None
            described.append(
                ModDescription(
                    name=entry.name,
                    enabled=entry.enabled,
                    version=resolved_version,
                    archives=mod_archives,
                    has_archive=has_archive,
                    is_core=is_core,
                    playable=has_archive or is_core,
                ),
            )
            listed.add(entry.name)
        # Surface bundled DLC the game reports even if it is absent from
        # mods-list.json, so it shows as installed/playable in the UI.
        for name, version in bundled.items():
            if name in listed:
                continue
            described.append(
                ModDescription(
                    name=name,
                    enabled=True,
                    version=version or None,
                    archives=[],
                    has_archive=False,
                    is_core=True,
                    playable=True,
                ),
            )
        return described

    def installed(self: Self) -> Generator[ServerModEntry]:
        yield from self.read_list()

    def active(self: Self) -> Generator[str]:
        for mod in self.installed():
            if mod.enabled:
                yield mod.name

