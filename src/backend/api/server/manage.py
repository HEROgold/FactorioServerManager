"""Server related management endpoints."""


import contextlib
from collections.abc import AsyncGenerator
from typing import NoReturn

import docker
import docker.errors
from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from backend.core.server import Server
from backend.models.factorio import ServerSettings
from backend.models.user import get_current_user


router = APIRouter()

@router.route("/update", methods=["POST"])
async def update(name: str, new_settings: ServerSettings) -> None:
    """Update a server."""
    user = await get_current_user()
    server = user.servers[name]
    server.settings = new_settings


@router.route("/delete", methods=["GET"])
async def delete(name: str) -> None:
    """Delete a server."""
    current_user = await get_current_user()
    server = current_user.servers[name]
    with contextlib.suppress(docker.errors.NotFound):
        server.remove()


@router.route("/start", methods=["POST"])
async def start(name: str) -> None:
    """Start a server through a http request."""
    current_user = await get_current_user()
    await current_user.servers[name].start()


@router.route("/stop", methods=["POST"])
async def stop(name: str) -> None:
    """Stop a server through a http request."""
    current_user = await get_current_user()
    await current_user.servers[name].stop()


@router.route("/restart", methods=["POST"])
async def restart(name: str) -> JSONResponse | None:
    """Restart a server through a http request."""
    current_user = await get_current_user()
    try:
        await current_user.servers[name].restart()
        current_user = await get_current_user()
    except RuntimeError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})


async def get_live_status(name: str) -> str:
    """Get the status of a server. without using cached data."""
    return Server(name=name, user=await get_current_user()).status

@router.route("/status/")
def status(name: str) -> None:
    """Stream the status of a server using SSE."""
    async def generate() -> AsyncGenerator[str, NoReturn]:
        previous_status = ""
        while True:
            status = await get_live_status(name)
            if status == previous_status:
                continue
            previous_status = status
            yield "event: serverStatusUpdate\n"
            yield f"data: {status}\n"
            yield "\n"
            return StreamingResponse(generate(), media_type="text/event-stream")


@router.route("/rcon", methods=["POST", "GET"])
async def rcon(name: str) -> None:
    """Return rcon data."""
    # TODO  # noqa: FIX002, TD002, TD003, TD004
