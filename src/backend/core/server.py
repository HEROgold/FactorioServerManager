"""Module to handle server operations."""
from __future__ import annotations  # avoid User is not defined in Server class

import json
import shutil
from functools import partial
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, Self

import docker
from constants import DOCKER_CONTAINER_PREFIX, PUBLIC_IP, SERVERS_DIRECTORY
from docker.errors import NotFound
from enums.states import DockerStates
from models.factorio import MapGenerationSettings, MapSettings, ServerSettings
from pydantic import BaseModel

from backend.core.DefaultSettings import DefaultServerSettings, default_map_settings


if TYPE_CHECKING:
    from collections.abc import Generator

    from docker.models.containers import Container
    from models.factorio import ServerModEntry
    from models.user import User


docker_client = docker.from_env()


class Server(BaseModel):
    """Model for a server."""

    name: str
    user: User
    _PID: int | None = None
    _version: str | None = None
    _container: Container | None = None
    _settings: ServerSettings | None = None
    _ip: str | None = None
    _map_settings: MapSettings | None = default_map_settings
    _map_generation_settings: map_generation_settings_file | None = None

    @property
    def ip(self: Self) -> str:
        """Return the server's IP."""
        if not self._ip:
            self._ip = PUBLIC_IP or "localhost"
        return self._ip

    @property
    def server_directory(self: Self) -> Path:
        """Return the server's directory."""
        if self.user:
            return SERVERS_DIRECTORY / f"{self.user.id}/{self.name}"
        return SERVERS_DIRECTORY / f"dummy/{self.name}"

    @property
    def current_log_file(self: Self) -> Path:
        """Return the server's current log file Path."""
        return self.server_directory / "factorio-current.log"

    @property
    def previous_log_file(self: Self) -> Path:
        """Return the server's previous log file Path."""
        return self.server_directory / "factorio-previous.log"

    @property
    def config(self: Self) -> Path:
        """Return the server's config directory Path."""
        return self.server_directory / "config"

    @property
    def custom_settings_file(self: Self) -> Path:
        """Return the server's custom settings file Path."""
        return self.config / "custom-settings.json"

    @property
    def map_generation_settings_file(self: Self) -> Path:
        """Return the server's map generation settings file Path."""
        return self.config / "map-gen-settings.json"

    @property
    def map_settings_file(self: Self) -> Path:
        """Return the server's map settings file Path."""
        return self.config / "map-settings.json"

    @property
    def server_settings_file(self: Self) -> Path:
        """Return the server's server settings file Path."""
        return self.config / "server-settings.json"

    @property
    def server_whitelist_file(self: Self) -> Path:
        """Return the server's server whitelist file Path."""
        return self.config / "server-whitelist.json"

    @property
    def port(self: Self) -> int:
        """Return the server's port."""
        return self.settings.port

    @property
    def rcon_password(self: Self) -> str:
        """Return the server's RCON password."""
        with Path(self.config / "rconpw").open() as f:
            return f.read().strip()

    @property
    def mods(self: Self) -> Path:
        """Return the server's mods directory Path."""
        return self.server_directory / "mods"

    @property
    def mods_list(self: Self) -> Path:
        """Return the server's mods list file Path."""
        return self.server_directory / "mods-list.json"

    def get_installed_mods(self: Self) -> Generator[ServerModEntry]:
        """Return a generator of installed mods."""
        with self.mods_list.open() as f:
            data = json.load(f)
        yield from data["mods"]

    def get_active_mods(self: Self) -> Generator[str]:
        """Return a generator of active mods."""
        for mod in self.get_installed_mods():
            if mod.enabled:
                yield mod.name

    @property
    def saves(self: Self) -> Path:
        """Return the server's saves directory Path."""
        return self.server_directory / "saves"

    @property
    def scenarios(self: Self) -> Path:
        """Return the server's scenarios directory Path."""
        return self.server_directory / "scenarios"

    @property
    def script_output(self: Self) -> Path:
        """Return the server's script output directory Path."""
        return self.server_directory / "script-output"

    @property
    def settings(self: Self) -> ServerSettings:
        """Return the server's settings."""
        if self._settings:
            return self._settings
        self.settings = DefaultServerSettings(name=self.name)  # type: ignore[reportCallIssue]
        return self.settings

    @settings.setter
    def settings(self: Self, settings: ServerSettings) -> None:
        self._settings = settings

    @property
    def map_settings(self: Self) -> MapSettings:
        """Return the server's map settings."""
        if self._map_settings:
            return self._map_settings
        self.map_settings = default_map_settings
        return self.map_settings

    @map_settings.setter
    def map_settings(self: Self, settings: MapSettings) -> None:
        """Set the server's map settings."""
        self._map_settings = settings

    @property
    def map_generation_settings(self: Self) -> MapGenerationSettings:
        """Return the server's map generation settings."""
        if self._map_generation_settings:
            return self._map_generation_settings
        self.map_generation_settings = MapGenerationSettings()
        return self.map_generation_settings

    @map_generation_settings.setter
    def map_generation_settings(self: Self, settings: MapGenerationSettings) -> None:
        self._map_generation_settings = settings

    @property
    def version(self: Self) -> str:
        """ "Return the server's version."""
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

    @property
    def is_first_launch(self: Self) -> bool:
        """Return True if the server is being launched for the first time."""
        return not self.server_directory.exists()

    @property
    def container(self: Self) -> Container:
        """Return the server's docker container."""
        if self._container:
            return self._container
        self._container = docker_client.containers.get(self.get_container_name())
        return self.container

    def get_container_name(self: Self) -> str:
        """Return the server's container name."""
        if self.user:
            return f"{DOCKER_CONTAINER_PREFIX}_{self.user.id}_{self.name}"
        return f"{DOCKER_CONTAINER_PREFIX}_dummy_{self.name}"

    @property
    def status(self: Self) -> str:
        """Return the server's status."""
        try:
            return self.container.status
        except NotFound:
            return DockerStates.UNKNOWN.value

    async def create(self: Self, version: str = "latest") -> None:
        """Create the server."""
        if not self.is_first_launch:
            msg = "Server already exists"
            raise FileExistsError(msg)

        self.version = version

        def _pull_create(container_name: str, directory: Path) -> None:
            docker_client.images.pull("factoriotools/factorio", tag=version)  # Naively pull, to ensure we have it.
            docker_client.containers.create(
                image=f"factoriotools/factorio:{version}",
                detach=True,
                ports={"34197/udp": self.port, "27015/tcp": 27015},
                volumes=[
                    f"{directory}:/factorio",
                ],
                name=container_name,
                restart_policy={"Name": "on-failure", "MaximumRetryCount": 2},
            )

        self.server_directory.mkdir(parents=True, exist_ok=True)
        self.custom_settings_file.write_text(self.settings.model_dump_json())
        t = Thread(target=_pull_create, args=[self.get_container_name(), self.server_directory])
        t.daemon = True
        t.start()

    async def start(self: Self) -> None:
        """Use a new thread to start the server."""
        if self.container.status == DockerStates.RUNNING.value:
            msg = "Server already running"
            raise RuntimeError(msg)
        p = partial(self.container.start)
        t = Thread(target=p)
        t.daemon = True
        t.start()

    async def stop(self: Self) -> None:
        """Use a new thread to stop the server."""
        if self.container.status == DockerStates.EXITED.value:
            msg = "Server already stopped"
            raise RuntimeError(msg)
        p = partial(self.container.stop)
        t = Thread(target=p)
        t.daemon = True
        t.start()

    async def restart(self: Self) -> None:
        """Use a new thread to restart the server."""
        if self.container.status == DockerStates.EXITED.value:
            msg = "Server not running"
            raise RuntimeError(msg)
        if self.container.status == DockerStates.RESTARTING.value:
            msg = "Server busy restarting"
            raise RuntimeError(msg)
        p: partial[None] = partial(self.container.restart)
        t = Thread(target=p)
        t.daemon = True
        t.start()

    def remove(self: Self) -> None:
        """Remove the server and its directory."""
        s = self.server_directory
        shutil.rmtree(s)
        self.container.stop()
        self.container.remove()
        del self
