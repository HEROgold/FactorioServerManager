import logging
import shutil
import stat
from pathlib import Path
from typing import TYPE_CHECKING, Self

import httpxyz

from api._types.backends import ServerSpec, get_backend
from api._types.enums import DockerStates
from api._types.server.files import ServerFiles
from api._types.server.mods import ServerMods
from api._types.server.server_settings import ServerSettings
from api.constants import (
    DEFAULT_VERSION,
    DOCKER_CONTAINER_PREFIX,
    RELEASES_URL,
    AppConfig,
)
from api.utils import sanitize_str

if TYPE_CHECKING:
    from api._types.database import User

logger = logging.getLogger(__name__)

# Release channels the download UI offers in place of a concrete version. The
# mod portal (and any version-pinned tooling) needs a real number, so these are
# resolved against the official latest-releases API before being persisted.
VERSION_CHANNELS = ("latest", "stable", "experimental")


async def resolve_factorio_version(version: str) -> str:
    """Resolve a release channel to a concrete headless version number.

    ``stable`` resolves to the current stable headless build; ``latest`` and
    ``experimental`` to the current experimental build. A value that is not a
    known channel (e.g. an explicit ``2.0.55``) is returned unchanged. If the
    lookup fails (e.g. no network) the original value is returned so server
    creation is never blocked.
    """
    if version not in VERSION_CHANNELS:
        return version
    bucket = "stable" if version == "stable" else "experimental"
    try:
        async with httpxyz.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(RELEASES_URL)
            resp.raise_for_status()
            payload = resp.json()
    except (httpxyz.HTTPError, ValueError):
        return version
    resolved = payload.get(bucket, {}).get("headless") if isinstance(payload, dict) else None
    return resolved or version


class Server:
    _version: str | None = None
    _port: int | None = None

    def __init__(self: Self, name: str, user: User, port: int | None = None) -> None:
        self._port = port
        # Defence in depth: every server name is reduced to a safe [A-Za-z0-9_-]
        # slug here, so no code path can build a Server (and thus host paths /
        # container names) from an unsanitised name.
        self._name = sanitize_str(name)
        self._user = user
        self.files = ServerFiles(self)
        self.mods = ServerMods(self)
        self.settings = ServerSettings(self)
        # Display/connect address shown to players (public). RCON is dialled by
        # the manager via rcon_host, which may be a private address so the RCON
        # port never needs to be public.
        self.ip = AppConfig.PUBLIC_IP or "localhost"
        self.rcon_host = AppConfig.RCON_HOST or self.ip

    @property
    def user(self: Self) -> User:
        return self._user

    @property
    def name(self: Self) -> str:
        return self._name

    @property
    def port(self: Self) -> int:
        """UDP game port. A launch parameter, not part of server-settings.json."""
        return self._port or 34197

    @property
    def rcon_password(self: Self) -> str:
        with self.files.rconpw.open() as f:
            return f.read().strip()

    @property
    def version(self: Self) -> str:
        if self._version:
            return self._version
        msg = "Version not set"
        raise AttributeError(msg)

    @version.setter
    def version(self: Self, value: str) -> None:
        if self._version:
            msg = "Version already set"
            raise AttributeError(msg)
        self._version = value

    def persist_version(self: Self, version: str) -> None:
        self.files.version.parent.mkdir(parents=True, exist_ok=True)
        self.files.version.write_text(f"{version.strip()}\n")

    def _read_persisted_version(self: Self) -> str | None:
        if self.files.version.exists():
            value = self.files.version.read_text().strip()
            if value:
                return value
        return None

    @property
    def factorio_version(self: Self) -> str:
        if self._version:
            return self._version
        if version := self._read_persisted_version():
            self._version = version
            return version
        msg = "Version not set and could not be determined from persisted data"
        raise AttributeError(msg)

    @property
    def factorio_version_line(self: Self) -> str | None:
        """The ``major.minor`` line (e.g. ``2.0``) used to filter the mod portal.

        Returns ``None`` for a non-numeric version -- such as an unresolved
        release channel like ``stable`` persisted by an older create -- so
        callers never feed an invalid ``version`` filter to the portal.
        """
        try:
            version = self.factorio_version
        except AttributeError:
            return None
        major, _, rest = version.partition(".")
        minor = rest.partition(".")[0]
        if not (major.isdigit() and minor.isdigit()):
            return None
        return f"{major}.{minor}"

    @property
    def is_first_launch(self: Self) -> bool:
        return not self.files.directory.exists()

    def get_container_name(self: Self) -> str:
        # pyrefly: ignore [redundant-condition]
        if self.user:
            return f"{DOCKER_CONTAINER_PREFIX}_{self.user.id}_{self.name}"
        return f"{DOCKER_CONTAINER_PREFIX}_dummy_{self.name}"

    @property
    def spec(self: Self) -> ServerSpec:
        """Build the backend-agnostic spec for this server."""
        return ServerSpec(
            name=self.name,
            identifier=self.get_container_name(),
            version=self._version or self._read_persisted_version() or DEFAULT_VERSION,
            game_port=self.port,
            rcon_port=AppConfig.RCON_PORT,
            data_dir=self.files.directory,
        )

    @property
    def status(self: Self) -> str:
        return get_backend().status(self.spec)

    async def create(self: Self, version: str = DEFAULT_VERSION) -> None:
        if not self.is_first_launch:
            msg = "Server already exists"
            raise FileExistsError(msg)

        # Pin release channels ("stable"/"latest") to a concrete version number
        # so the persisted version is usable as a mod-portal filter, not a label.
        resolved = await resolve_factorio_version(version)
        self.version = resolved
        self.files.directory.mkdir(parents=True, exist_ok=True)
        # Write the real Factorio config files the headless server reads on boot.
        self.settings.write_all()
        self.persist_version(resolved)
        await get_backend().create(self.spec)

    async def start(self: Self) -> None:
        """Start the server via the configured backend."""
        if self.status == DockerStates.RUNNING.value:
            msg = "Server already running"
            raise RuntimeError(msg)
        await get_backend().start(self.spec)

    async def stop(self: Self) -> None:
        """Stop the server via the configured backend."""
        if self.status == DockerStates.EXITED.value:
            msg = "Server already stopped"
            raise RuntimeError(msg)
        await get_backend().stop(self.spec)

    async def restart(self: Self) -> None:
        """Restart the server via the configured backend."""
        if self.status == DockerStates.EXITED.value:
            msg = "Server not running"
            raise RuntimeError(msg)
        if self.status == DockerStates.RESTARTING.value:
            msg = "Server busy restarting"
            raise RuntimeError(msg)
        await get_backend().restart(self.spec)

    async def remove(self: Self) -> None:
        """Remove the server's backend resources and on-disk data.

        Removal must be reliable: the dashboard lists servers by enumerating
        their on-disk directories, so a directory that survives keeps the server
        visible in the UI. ``ignore_errors`` would hide a partial failure and
        report success while leaving the directory behind — the exact cause of
        "deleted server still appears". The common failures are a read-only file
        attribute (Windows dev) and, in production, files written by the Factorio
        container under a different uid that the unprivileged backend cannot
        remove (mitigated by passing PUID/PGID at container creation). We clear
        the read-only bit and retry, log anything we still cannot delete, then
        verify the directory is actually gone so the caller surfaces a real error
        instead of a false success.
        """
        await get_backend().remove(self.spec)

        directory = self.files.directory
        if not directory.exists():
            return

        def _on_error(func, path, _exc) -> None:  # noqa: ANN001
            # First failure is often just a read-only attribute; clear it and
            # retry the operation (unlink / rmdir) that raised. If it still
            # fails (e.g. cross-uid ownership the backend can't override), log
            # and re-raise so rmtree aborts and the failure is not swallowed.
            try:
                Path(path).chmod(stat.S_IWRITE)
                func(path)
            except OSError:
                logger.warning("Could not remove %s while deleting %s", path, directory, exc_info=True)
                raise

        try:
            shutil.rmtree(directory, onexc=_on_error)
        except OSError as err:
            msg = f"Server directory {directory} could not be fully removed"
            logger.exception(msg)
            raise RuntimeError(msg) from err

        if directory.exists():
            msg = f"Server directory {directory} could not be fully removed"
            logger.error(msg)
            raise RuntimeError(msg)
