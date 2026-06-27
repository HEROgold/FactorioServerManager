"""Common interface for the orchestrators that spawn Factorio servers.

A backend turns a :class:`ServerSpec` into a running Factorio server. Two
implementations exist - Docker and Kubernetes - selected at runtime via
:data:`api.constants.AppConfig.SERVER_BACKEND` (an :class:`BackendKind`).
Statuses are normalised to the :class:`api._types.enums.DockerStates` vocabulary
so callers do not need to know which backend is in use.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class ServerSpec:
    """Everything a backend needs to manage one Factorio server."""

    name: str
    """Human-readable server name."""
    identifier: str
    """Unique resource name (container / deployment name)."""
    version: str
    """Factorio version, used as the image tag."""
    game_port: int
    """UDP port the game is exposed on."""
    rcon_port: int
    """TCP port the RCON interface is exposed on."""
    data_dir: Path
    """Host directory mounted at ``/factorio`` (Docker) or backing the volume (K8s)."""


@runtime_checkable
class ServerBackend(Protocol):
    """Protocol implemented by every server orchestration backend."""

    async def create(self, spec: ServerSpec) -> None:
        """Provision the server (pull image, create container/deployment)."""
        ...

    async def start(self, spec: ServerSpec) -> None:
        """Start a previously created server."""
        ...

    async def stop(self, spec: ServerSpec) -> None:
        """Stop a running server."""
        ...

    async def restart(self, spec: ServerSpec) -> None:
        """Restart a running server."""
        ...

    async def remove(self, spec: ServerSpec) -> None:
        """Remove the server's orchestration resources."""
        ...

    def status(self, spec: ServerSpec) -> str:
        """Return the server status as a ``DockerStates`` value."""
        ...
