"""Server lifecycle API routes (info/create/start/stop/restart/delete/status)."""

from __future__ import annotations

import asyncio
from logging import getLogger
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from api._types.database import User
from api._types.server.core import Server as DataServer
from api.constants import SSE_HEADERS, AppConfig
from api.deps import get_current_user
from api.routers.server.shared import _get_server_or_404, _safe_version
from api.utils import sanitize_str

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = getLogger(__name__)

router = APIRouter()


@router.get("/server/{name}")
async def get_server(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Return server metadata for the named server."""
    server = _get_server_or_404(current_user, name)
    return {
        "name": server.name,
        "port": server.port,
        "ip": server.ip,
        "status": server.status,
        "factorio_version": _safe_version(server),
        "mods": server.mods.describe(),
    }


class PortLimits(BaseModel):
    """Configured game-port range plus an in-range default the UI can pre-fill."""

    lower: int
    upper: int
    default: int


# The Factorio default game port. Used as the suggested value when it falls
# inside the configured range, otherwise the range is clamped over it.
DEFAULT_GAME_PORT = 34197


@router.get("/port-limits", response_model=PortLimits)
async def port_limits() -> PortLimits:
    """Expose the game-port range so the create form can bound and clamp input.

    The limits are operator-configurable (``AppConfig.LOWER_PORT_LIMIT`` /
    ``UPPER_PORT_LIMIT``); without this the UI hardcodes 1-65535 and cannot know
    the real bounds. ``default`` is the Factorio default clamped into range so a
    left-blank field still yields a valid port.
    """
    lower, upper = AppConfig.LOWER_PORT_LIMIT, AppConfig.UPPER_PORT_LIMIT
    default = min(max(DEFAULT_GAME_PORT, lower), upper)
    return PortLimits(lower=lower, upper=upper, default=default)


@router.post("/server/{name}/create", status_code=201)
async def create_server(
    name: str,
    version: str,
    current_user: Annotated[User, Depends(get_current_user)],
    port: int | None = None,
) -> dict:
    """Create a new Factorio server for the current user."""
    lower, upper = AppConfig.LOWER_PORT_LIMIT, AppConfig.UPPER_PORT_LIMIT
    if port is not None and not (lower <= port <= upper):
        raise HTTPException(
            status_code=422,
            detail=f"port must be between {lower} and {upper}",
        )
    name = sanitize_str(name)
    server = DataServer(name, current_user, port)

    if (err := current_user.add_server(server)):
        raise HTTPException(status_code=409, detail=str(err)) from err

    server = current_user.servers[name]
    await server.create(version)
    return {"detail": "created", "name": name}


async def _run_server_action(current_user: User, name: str, action: str, status: str) -> dict:
    server = _get_server_or_404(current_user, name)
    await getattr(server, action)()
    return {"status": status}


@router.post("/server/{name}/start")
async def start_server(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Start the named server."""
    return await _run_server_action(current_user, name, "start", "started")


@router.post("/server/{name}/stop")
async def stop_server(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Stop the named server."""
    return await _run_server_action(current_user, name, "stop", "stopped")


@router.post("/server/{name}/restart")
async def restart_server(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Restart the named server."""
    server = _get_server_or_404(current_user, name)
    try:
        await server.restart()
    except RuntimeError as e:
        logger.exception("Failed to restart server %s", name)
        raise HTTPException(status_code=400, detail="Failed to change the server state.") from e
    return {"status": "restarted"}


@router.delete("/server/{name}")
async def delete_server(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    """Delete the named server (best-effort)."""
    server = _get_server_or_404(current_user, name)
    try:
        await server.remove()
    except Exception as err:
        # best-effort removal
        raise HTTPException(status_code=500, detail="Failed to remove server") from err
    return JSONResponse(status_code=204, content={})


@router.get("/server/{name}/status")
async def status_stream(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """Server status Server-Sent-Events stream."""
    async def generate() -> AsyncGenerator[str]:
        previous_status = None
        while True:
            try:
                status = current_user.servers[name].status
            except (KeyError, AttributeError):
                status = "unknown"
            if status and status == previous_status:
                await asyncio.sleep(0.5)
                continue
            previous_status = status
            yield "event: serverStatusUpdate\n"
            yield f"data: {status}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)
