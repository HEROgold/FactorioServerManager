from typing import TypedDict


class Route(TypedDict):
    name: str
    path: str

class ServerModEntry(TypedDict):
    name: str
    enabled: bool
