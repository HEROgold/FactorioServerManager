"""Domain types for the fsm API."""

from .factorio_interface import FactorioInterface


class Version(str):
    """Represents a Factorio version string."""

    __slots__ = ()


__all__ = [
    "FactorioInterface",
    "Version",
]
