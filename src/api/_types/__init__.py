"""Domain types for the fsm API."""

from .factorio_interface import FactorioInterface
from .factorio_interface import FactorioInterface as FactorioBridge


class Version(str):
    """Represents a Factorio version string."""

    __slots__ = ()


__all__ = [
    "FactorioBridge",
    "FactorioInterface",
    "Version",
]
