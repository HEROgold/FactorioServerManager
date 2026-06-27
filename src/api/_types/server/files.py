from typing import TYPE_CHECKING, Self

from api.constants import SERVERS_DIRECTORY

if TYPE_CHECKING:
    from pathlib import Path

    from api._types.server.core import Server


class ServerFiles:
    """All on-disk paths for a server, namespaced under ``server.files``.

    Holds a back-reference to the owning Server because most paths derive from its
    identity (name, user id) and the mods directory is resolved through the active
    backend via the shared mod store.
    """

    def __init__(self: Self, server: Server) -> None:
        self._server = server

    @property
    def directory(self: Self) -> Path:
        # pyrefly: ignore [redundant-condition]
        if self._server.user:
            return SERVERS_DIRECTORY / f"{self._server.user.id}/{self._server.name}"
        return SERVERS_DIRECTORY / f"dummy/{self._server.name}"

    @property
    def config(self: Self) -> Path:
        return self.directory / "config"

    @property
    def saves(self: Self) -> Path:
        return self.directory / "saves"

    @property
    def scenarios(self: Self) -> Path:
        return self.directory / "scenarios"

    @property
    def script_output(self: Self) -> Path:
        return self.directory / "script-output"

    @property
    def mods_dir(self: Self) -> Path:
        return self.directory / "mods"

    @property
    def mods_list(self: Self) -> Path:
        return self.mods_dir / "mods-list.json"

    @property
    def manager_meta(self: Self) -> Path:
        """Manager-specific metadata (public-display opt-in), not a Factorio file."""
        return self.directory / "manager.json"

    @property
    def current_log(self: Self) -> Path:
        return self.directory / "factorio-current.log"

    @property
    def previous_log(self: Self) -> Path:
        return self.directory / "factorio-previous.log"

    @property
    def custom_settings(self: Self) -> Path:
        return self.config / "custom-settings.json"

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
    def version(self: Self) -> Path:
        return self.config / "factorio-version.txt"

    @property
    def rconpw(self: Self) -> Path:
        return self.config / "rconpw"

