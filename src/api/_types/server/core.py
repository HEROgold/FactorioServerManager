import shutil
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
        self.ip = AppConfig.PUBLIC_IP or "localhost"

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
        """Remove the server's backend resources and on-disk data."""
        await get_backend().remove(self.spec)
        shutil.rmtree(self.files.directory, ignore_errors=True)
