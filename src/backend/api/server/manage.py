"""Server related management endpoints."""


import contextlib

import docker
import docker.errors
from fastapi import APIRouter, HTTPException

from backend.core.server import Server
from backend.enums.states import DockerStates
from backend.models.factorio import ServerSettings
from backend.models.user import get_current_user
from backend.utils.strings import sanitize


router = APIRouter(prefix="/manage")

@router.post("/create")
async def create(name: str, version: str, port: int) -> None:
    """Create a server."""
    user = await get_current_user()
    name = sanitize(name)

    server = Server(name=name, user=user)
    server.settings.port = port
    if not user.is_server_registered(server):
        msg = "Server is already registered."
        raise HTTPException(405, msg)
    if not user.can_add_server():
        msg = "User cannot add more servers."
        raise HTTPException(405, msg)
    user.add_server(server)

    await server.create(version)

@router.post("/update")
async def update(name: str, new_settings: ServerSettings) -> None:
    """Update a server."""
    user = await get_current_user()
    server = user.servers[name]
    server.settings = new_settings


@router.get("/delete")
async def delete(name: str) -> None:
    """Delete a server."""
    current_user = await get_current_user()
    server = current_user.servers[name]
    with contextlib.suppress(docker.errors.NotFound):
        server.remove()


@router.post("/start")
async def start(name: str) -> None:
    """Start a server through a http request."""
    current_user = await get_current_user()
    await current_user.servers[name].start()


@router.post("/stop")
async def stop(name: str) -> None:
    """Stop a server through a http request."""
    current_user = await get_current_user()
    await current_user.servers[name].stop()


@router.post("/restart")
async def restart(name: str) -> bool:
    """Restart a server through a http request."""
    current_user = await get_current_user()
    try:
        await current_user.servers[name].restart()
        current_user = await get_current_user()
    except RuntimeError as _:
        return False
    return True


@router.route("/rcon", methods=["POST", "GET"])
async def rcon(name: str) -> None:
    """Return rcon data."""
    # TODO  # noqa: FIX002, TD002, TD003, TD004


@router.get("/status")
async def status(name: str) -> DockerStates:
    """Return the status of a server."""
    current_user = await get_current_user()
    return current_user.servers[name].status
