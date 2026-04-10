"""Server-related API routes (create/start/stop/status/logs)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from FSM._types.data import Server as DataServer
from FSM.api.deps import get_current_user
from FSM.scripts import sanitize_str

if TYPE_CHECKING:
    from collections.abc import Generator

    from FSM._types.database import User

router = APIRouter()


def _get_server_or_404(user: User, name: str) -> DataServer:
    server = user.servers.get(name) if getattr(user, "servers", None) else None
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


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
        "factorio_version": server.factorio_version,
        "mods": server.describe_mods(),
    }


@router.post("/server/{name}/create", status_code=201)
async def create_server(
    name: str,
    version: str,
    current_user: Annotated[User, Depends(get_current_user)],
    port: int | None = None,
) -> dict:
    """Create a new Factorio server for the current user."""
    name = sanitize_str(name)
    server = DataServer(name, current_user)
    if port is not None:
        server.settings.port = int(port)
    current_user.add_server(server)
    server = current_user.servers[name]
    await server.create(version)
    return {"detail": "created", "name": name}


@router.post("/server/{name}/start")
async def start_server(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Start the named server."""
    server = _get_server_or_404(current_user, name)
    await server.start()
    return {"status": "started"}


@router.post("/server/{name}/stop")
async def stop_server(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Stop the named server."""
    server = _get_server_or_404(current_user, name)
    await server.stop()
    return {"status": "stopped"}


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
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"status": "restarted"}


@router.delete("/server/{name}")
async def delete_server(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    """Delete the named server (best-effort)."""
    server = _get_server_or_404(current_user, name)
    try:
        server.remove()
    except Exception as err:
        # best-effort removal
        raise HTTPException(status_code=500, detail="Failed to remove server") from err
    return JSONResponse(status_code=204, content={})


@router.get("/server/{name}/logs")
async def get_logs(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Return current and previous logs for the named server."""
    server = _get_server_or_404(current_user, name)
    current_log = (
        server.current_log_file.read_text(encoding="utf-8", errors="replace")
        if server.current_log_file.exists()
        else ""
    )
    previous_log = (
        server.previous_log_file.read_text(encoding="utf-8", errors="replace")
        if server.previous_log_file.exists()
        else ""
    )
    return {"current_log": current_log, "previous_log": previous_log}


@router.get("/server/{name}/status")
async def status_stream(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """Server status Server-Sent-Events stream."""
    def generate() -> Generator[str]:
        previous_status = None
        while True:
            try:
                status = current_user.servers[name].status
            except (KeyError, AttributeError):
                status = "unknown"
            if status and status == previous_status:
                time.sleep(0.5)
                continue
            previous_status = status
            yield f"data: {status}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
