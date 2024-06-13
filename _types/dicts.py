from typing import TypedDict


class Route(TypedDict):
    name: str
    path: str

class ServerModEntry(TypedDict):
    name: str
    enabled: bool


class SteerSettings(TypedDict):
    radius: float
    separation_force: float
    separation_factor: float
    force_unit_fuzzy_goto_behavior: bool


class AutoPlace(TypedDict):
    frequency: int
    size: int
    richness: int


class Coordinates(TypedDict):
    x: int
    y: int
