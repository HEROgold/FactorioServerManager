"""Docker implementation of :class:`ServerBackend`."""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING

import docker
from docker.errors import DockerException, NotFound

from api._types.backends import ServerBackend
from api._types.enums import DockerStates
from api.constants import AppConfig

if TYPE_CHECKING:
    from docker.models.containers import Container

    from api._types.backends.base import ServerSpec

# Keep references to fire-and-forget tasks so they are not garbage-collected.
_BACKGROUND_TASKS: set[asyncio.Task[None]] = set()


class DockerBackend(ServerBackend):
    """Spawn Factorio servers as containers on the local Docker daemon."""

    def __init__(self) -> None:
        try:
            self._client = docker.from_env()
        except DockerException as exc:
            msg = "Docker daemon unavailable. Start Docker and rerun the Factorio Server Manager."
            raise RuntimeError(msg) from exc

    def _container(self, identifier: str) -> Container:
        return self._client.containers.get(identifier)

    def status(self, spec: ServerSpec) -> str:
        try:
            return self._container(spec.identifier).status
        except NotFound:
            return DockerStates.UNKNOWN.value

    async def create(self, spec: ServerSpec) -> None:
        image: str = AppConfig.FACTORIO_IMAGE

        def _pull_create() -> None:
            # Naively pull to ensure the tag is present locally.
            self._client.images.pull(image, tag=spec.version)
            self._client.containers.create(
                image=f"{image}:{spec.version}",
                detach=True,
                ports={"34197/udp": spec.game_port, "27015/tcp": spec.rcon_port},
                volumes=[f"{spec.data_dir}:/factorio"],
                name=spec.identifier,
                restart_policy={"Name": "on-failure", "MaximumRetryCount": 2},
            )

        # Image pulls can take minutes; run in the background and return.
        task = asyncio.create_task(asyncio.to_thread(_pull_create))
        _BACKGROUND_TASKS.add(task)
        task.add_done_callback(_BACKGROUND_TASKS.discard)

    async def start(self, spec: ServerSpec) -> None:
        await asyncio.to_thread(self._container(spec.identifier).start)

    async def stop(self, spec: ServerSpec) -> None:
        await asyncio.to_thread(self._container(spec.identifier).stop)

    async def restart(self, spec: ServerSpec) -> None:
        await asyncio.to_thread(self._container(spec.identifier).restart)

    async def remove(self, spec: ServerSpec) -> None:
        def _remove() -> None:
            with contextlib.suppress(NotFound):
                container = self._container(spec.identifier)
                container.stop()
                container.remove()

        await asyncio.to_thread(_remove)
