"""Server RCON API routes (connection details + running commands)."""

from __future__ import annotations

import asyncio
import contextlib
from logging import getLogger
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api._types.database import User
from api._types.enums import DockerStates
from api._types.rcon import RconError
from api._types.rcon import execute as rcon_execute
from api.constants import AppConfig
from api.deps import get_current_user
from api.routers.server.shared import _get_server_or_404

logger = getLogger(__name__)

router = APIRouter()


@router.get("/server/{name}/rcon")
async def rcon(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Return RCON connection details for the named server."""
    server = _get_server_or_404(current_user, name)
    password = None
    with contextlib.suppress(OSError):
        password = server.rcon_password
    return {
        "host": server.ip,
        "port": AppConfig.RCON_PORT,
        "password": password,
    }


class RconCommand(BaseModel):
    """An RCON command to run against a running server."""

    command: str


@router.post("/server/{name}/rcon/send")
async def rcon_send(
    name: str,
    payload: RconCommand,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Run a single RCON command on the named server and return its response."""
    server = _get_server_or_404(current_user, name)
    if server.status != DockerStates.RUNNING.value:
        raise HTTPException(status_code=409, detail="Server is not running")

    command = payload.command.strip()
    if not command:
        raise HTTPException(status_code=400, detail="Command must not be empty")

    try:
        password = server.rcon_password
    except OSError as err:
        raise HTTPException(
            status_code=400,
            detail="RCON password not available; start the server once to generate it",
        ) from err

    try:
        async with asyncio.timeout(AppConfig.TIMEOUT_RCON):
            response = await rcon_execute(server.rcon_host, AppConfig.RCON_PORT, password, command)
    except RconError as err:
        logger.exception("RCON command failed for server %s", name)
        raise HTTPException(status_code=502, detail="RCON command failed.") from err
    return {"response": response}
