"""Docker implementation of :class:`ServerBackend`."""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING

import docker
from docker.errors import DockerException, NotFound

from api._types.backends import ServerBackend
from api._types.enums import DockerStates
from api.constants import FSM_GID, FSM_UID, AppConfig

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

        # Make Factorio write its data as the backend's service uid/gid so the
        # backend owns (and can delete) the server directory. The factoriotools
        # image chowns /factorio to PUID/PGID at startup and runs as that user;
        # without this it defaults to uid 845 and leaves files the backend cannot
        # remove. FSM_UID/FSM_GID resolve to the FSM_UID/FSM_GID env (set by the
        # Dockerfile/compose) or the backend process's own id on POSIX — the same
        # id docker-entrypoint.sh chowns the tree to and drops privileges to.
        environment: dict[str, str] = {"PUID": str(FSM_UID), "PGID": str(FSM_GID)}

        def _pull_create() -> None:
            # Naively pull to ensure the tag is present locally.
            self._client.images.pull(image, tag=spec.version)
            self._client.containers.create(
                image=f"{image}:{spec.version}",
                detach=True,
                ports={
                    "34197/udp": spec.game_port,
                    # Publish RCON on the configured host interface only
                    # (loopback by default) so the console port is not exposed
                    # on a public interface.
                    "27015/tcp": (AppConfig.RCON_BIND_HOST, spec.rcon_port),
                },
                volumes=[f"{spec.data_dir}:/factorio"],
                environment=environment,
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
