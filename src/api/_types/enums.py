
from enum import Enum, StrEnum


class DockerStates(Enum):
    CREATED = "created"
    RUNNING = "running"
    RESTARTING = "restarting"
    EXITED = "exited"
    PAUSED = "paused"
    DEAD = "dead"
    UNKNOWN = "unknown"


class BackendKind(StrEnum):
    """Which orchestrator spawns Factorio servers."""

    DOCKER = "docker"
    KUBERNETES = "kubernetes"
