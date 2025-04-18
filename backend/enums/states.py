"""Enum for different states."""
from enum import Enum


class DockerStates(Enum):
    """Enum for different container states."""

    CREATED = "created"
    RUNNING = "running"
    RESTARTING = "restarting"
    EXITED = "exited"
    PAUSED = "paused"
    DEAD = "dead"
    UNKNOWN = "unknown"
