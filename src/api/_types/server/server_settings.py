
from __future__ import annotations

from typing import TYPE_CHECKING, Self

from api._types.settings import GameSettings, MapGenerationSettings, MapSettings

if TYPE_CHECKING:
    from api._types.server.core import Server


class ServerSettings:
    """Grouping of the three Factorio settings documents under ``server.settings``.

    Each document is lazily initialized with a sensible default and can be
    replaced via its setter (e.g. after loading from disk).
    """

    def __init__(self: Self, server: Server) -> None:
        self._server = server
        self.game = GameSettings(name=server.name)
        self.map = MapSettings()
        self.map_generation = MapGenerationSettings()

    def write_all(self: Self) -> None:
        """Persist all three documents to their files in ``server.files``."""
        files = self._server.files
        self.game.name = self.game.name or self._server.name
        self.game.write(files.server_settings)
        self.map.write(files.map_settings)
        self.map_generation.write(files.map_generation_settings)
