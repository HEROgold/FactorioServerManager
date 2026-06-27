from __future__ import annotations  # avoid User is not defined in Server class

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

from api._types.backends import ServerSpec, get_backend
from api._types.dicts import ServerModEntry
from api._types.enums import DockerStates
from api._types.settings import MapGenerationSettings, MapSettings, ServerSettings
from api.constants import DOCKER_CONTAINER_PREFIX, SERVERS_DIRECTORY, AppConfig

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from api._types.database import User

@dataclass
class ModDescription:
    name: str
    enabled: bool
    version: str | None
    archives: list[ModArchive]
    has_archive: bool
    is_core: bool

@dataclass
class ModArchive:
    version: str
    filename: str
    size_bytes: int
    size_label: str

@dataclass
class Server:
    name: str
    user: User
    _PID: int | None = None
    _version: str | None = None
    _port: int | None = None
    _settings: ServerSettings | None = None
    _ip: str | None = None
    _map_settings: MapSettings | None = None
    _map_generation_settings: MapGenerationSettings | None = None

    @property
    def ip(self: Self) -> str:
        if not self._ip:
            self._ip = AppConfig.PUBLIC_IP or "localhost"
        return self._ip

    @property
    def server_directory(self: Self) -> Path:
        # pyrefly: ignore [redundant-condition]
        if self.user:
            return SERVERS_DIRECTORY / f"{self.user.id}/{self.name}"
        return SERVERS_DIRECTORY / f"dummy/{self.name}"

    @property
    def current_log_file(self: Self) -> Path:
        return self.server_directory / "factorio-current.log"

    @property
    def previous_log_file(self: Self) -> Path:
        return self.server_directory / "factorio-previous.log"

    @property
    def config(self: Self) -> Path:
        return self.server_directory / "config"

    @property
    def custom_settings_file(self: Self) -> Path:
        return self.config / "custom-settings.json"

    @property
    def map_generation_settings_file(self: Self) -> Path:
        return self.config / "map-gen-settings.json"

    @property
    def map_settings_file(self: Self) -> Path:
        return self.config / "map-settings.json"

    @property
    def server_settings_file(self: Self) -> Path:
        return self.config / "server-settings.json"

    @property
    def server_whitelist_file(self: Self) -> Path:
        return self.config / "server-whitelist.json"

    @property
    def port(self: Self) -> int:
        """UDP game port. A launch parameter, not part of server-settings.json."""
        return self._port or 34197

    @port.setter
    def port(self: Self, value: int) -> None:
        self._port = value

    @property
    def rcon_password(self: Self) -> str:
        with Path(self.config / "rconpw").open() as f:
            return f.read().strip()

    @property
    def mods(self: Self) -> Path:
        return self.server_directory / "mods"

    @property
    def mods_list(self: Self) -> Path:
        return self.server_directory / "mods-list.json"

    @property
    def version_file(self: Self) -> Path:
        return self.config / "factorio-version.txt"

    def ensure_mods_workspace(self: Self) -> None:
        self.mods.mkdir(parents=True, exist_ok=True)
        if not self.mods_list.exists():
            default = {"mods": [{"name": "base", "enabled": True}]}
            with self.mods_list.open("w") as f:
                json.dump(default, f, indent=2)

    def read_mod_list(self: Self) -> list[ServerModEntry]:
        self.ensure_mods_workspace()
        with self.mods_list.open() as f:
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
            self.write_mod_list(mods)
        return mods

    def write_mod_list(self: Self, mods: Iterable[ServerModEntry]) -> None:
        """Write the given list of mods to the mods-list.json file."""
        self.ensure_mods_workspace()
        normalized: list[ServerModEntry] = list(mods)
        if not any(mod.name == "base" for mod in normalized):
            normalized.insert(0, ServerModEntry(name="base", enabled=True))
        serializable = [
            {"name": mod.name, "enabled": mod.enabled}
            | ({"version": mod.version} if mod.version else {})
            for mod in normalized
        ]
        with self.mods_list.open("w") as f:
            json.dump({"mods": serializable}, f, indent=2)

    def upsert_mod_entry(self: Self, name: str, *, enabled: bool, version: str | None = None) -> None:
        mods = self.read_mod_list()
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
        self.write_mod_list(mods)

    def remove_mod_entry(self: Self, name: str) -> None:
        mods = [mod for mod in self.read_mod_list() if mod.name != name]
        self.write_mod_list(mods)

    def remove_mod_archives(self: Self, name: str) -> None:
        if not self.mods.exists():
            return
        for archive in self.mods.glob(f"{name}_*.zip"):
            archive.unlink(missing_ok=True)

    def _discover_mod_archives(self: Self) -> dict[str, list[ModArchive]]:
        if not self.mods.exists():
            return {}

        archives: dict[str, list[ModArchive]] = {}
        for archive in self.mods.glob("*.zip"):
            parsed = self._split_mod_archive_name(archive.name)
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
    def _split_mod_archive_name(filename: str) -> tuple[str, str] | None:
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

    def describe_mods(self: Self) -> list[ModDescription]:
        entries = self.read_mod_list()
        archives = self._discover_mod_archives()
        described: list[ModDescription] = []
        for entry in entries:
            mod_archives = archives.get(entry.name, [])
            mod_archives.sort(key=lambda item: self._version_key(item.version), reverse=True)
            resolved_version = entry.version
            if not resolved_version and mod_archives:
                resolved_version = mod_archives[0].version
            described.append(
                ModDescription(
                    name=entry.name,
                    enabled=entry.enabled,
                    version=resolved_version,
                    archives=mod_archives,
                    has_archive=bool(mod_archives),
                    is_core=entry.name == "base",
                ),
            )
        return described

    def get_installed_mods(self: Self) -> Generator[ServerModEntry]:
        yield from self.read_mod_list()

    def get_active_mods(self: Self) -> Generator[str]:
        for mod in self.get_installed_mods():
            if mod.enabled:
                yield mod.name

    @property
    def saves(self: Self) -> Path:
        return self.server_directory / "saves"

    @property
    def scenarios(self: Self) -> Path:
        return self.server_directory / "scenarios"

    @property
    def script_output(self: Self) -> Path:
        return self.server_directory / "script-output"

    @property
    def settings(self: Self) -> ServerSettings:
        if self._settings:
            return self._settings
        self.settings = ServerSettings(name=self.name)
        return self.settings

    @settings.setter
    def settings(self: Self, settings: ServerSettings) -> None:
        self._settings = settings

    @property
    def map_settings(self: Self) -> MapSettings:
        if self._map_settings:
            return self._map_settings
        self.map_settings = MapSettings()
        return self.map_settings

    @map_settings.setter
    def map_settings(self: Self, settings: MapSettings) -> None:
        self._map_settings = settings

    @property
    def map_generation_settings(self: Self) -> MapGenerationSettings:
        if self._map_generation_settings:
            return self._map_generation_settings
        self.map_generation_settings = MapGenerationSettings()
        return self.map_generation_settings

    @map_generation_settings.setter
    def map_generation_settings(self: Self, settings: MapGenerationSettings) -> None:
        self._map_generation_settings = settings

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
        self.version_file.parent.mkdir(parents=True, exist_ok=True)
        self.version_file.write_text(f"{version.strip()}\n")

    def _read_persisted_version(self: Self) -> str | None:
        if self.version_file.exists():
            value = self.version_file.read_text().strip()
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
        if version := self.factorio_version:
            parts = version.split(".")
            return ".".join(parts[:2])
        return None

    @property
    def is_first_launch(self: Self) -> bool:
        return not self.server_directory.exists()

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
            version=self._version or self._read_persisted_version() or "stable",
            game_port=self.port,
            rcon_port=AppConfig.RCON_PORT,
            data_dir=self.server_directory,
        )

    @property
    def status(self: Self) -> str:
        return get_backend().status(self.spec)

    async def create(self: Self, version: str = "stable") -> None:
        if not self.is_first_launch:
            msg = "Server already exists"
            raise FileExistsError(msg)

        self.version = version
        self.server_directory.mkdir(parents=True, exist_ok=True)
        # Write the real Factorio config files the headless server reads on boot.
        self.settings.name = self.settings.name or self.name
        self.settings.write(self.server_settings_file)
        self.map_settings.write(self.map_settings_file)
        self.map_generation_settings.write(self.map_generation_settings_file)
        self.persist_version(version)
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
        shutil.rmtree(self.server_directory, ignore_errors=True)
