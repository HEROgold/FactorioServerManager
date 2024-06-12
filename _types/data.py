import json
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from _types.database import User
from _types.dicts import ServerModEntry
from config import SERVERS_DIRECTORY


@dataclass
class ServerSettings:
    name: str
    password: str | None

    port: int = 34197
    description: str = ""
    tags: str = ""
    visibility_public: bool = False
    visibility_steam: bool = False
    visibility_lan: bool = True
    verify_user_identity: bool = True
    use_authserver_bans: bool = True
    whitelist: bool = True
    max_players: int = 10
    ignore_limit_returning: bool = True
    admins: str = ""
    allow_lua_commands: bool = True
    admin_pause: bool = True
    afk_autokick_timer: int = 0
    max_upload_speed: int = 2000
    max_upload_slots: int = 5
    autosave_interval: int = 3600
    autosave_only_on_server: bool = True


@dataclass
class Server:
    name: str
    user: User | None = None
    _settings: ServerSettings | None = None
    _PID: int | None = None

    @property
    def server_directory(self: Self) -> Path:
        if self.user:
            return SERVERS_DIRECTORY / f"{self.user.id}/{self.name}"
        return SERVERS_DIRECTORY / f"dummy/{self.name}"

    @property
    def current_log(self: Self) -> Path:
        return self.server_directory / "factorio-current.log"

    @property
    def previous_log(self: Self) -> Path:
        return self.server_directory / "factorio-previous.log"

    @property
    def config(self: Self) -> Path:
        return self.server_directory / "config"

    @property
    def map_generation_settings(self: Self) -> Path:
        return self.config / "map-gen-settings.json"

    @property
    def map_settings(self: Self) -> Path:
        return self.config / "map-settings.json"

    @property
    def server_settings(self: Self) -> Path:
        return self.config / "server-settings.json"

    @property
    def server_whitelist(self: Self) -> Path:
        return self.config / "server-whitelist.json"

    @property
    def port(self: Self) -> int:
        return 34197

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

    def get_installed_mods(self: Self) -> Generator[ServerModEntry, None, None]:
        with self.mods_list.open() as f:
            data = json.load(f)
        yield from data["mods"]

    def get_active_mods(self: Self) -> Generator[str, None, None]:
        for mod in self.get_installed_mods():
            if mod["enabled"]:
                yield mod["name"]

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
        self.settings = ServerSettings(self.name, None)
        return self.settings

    @settings.setter
    def settings(self: Self, settings: ServerSettings) -> None:
        self._settings = settings

    @property
    def process_id(self: Self) -> int:
        if self._PID:
            return self._PID
        msg = "PID not set"
        raise AttributeError(msg)

    @process_id.setter
    def process_id(self: Self, value: int) -> None:
        self._PID = value

    def is_first_launch(self: Self) -> bool:
        if self.server_directory.exists():
            return False
        return True
