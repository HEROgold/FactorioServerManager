"""Server-related API routes (create/start/stop/status/logs/settings/rcon)."""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import asdict
from typing import TYPE_CHECKING, Annotated

import httpxyz
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api._types.database import User
from api._types.enums import DockerStates
from api._types.rcon import RconError
from api._types.rcon import execute as rcon_execute
from api._types.server.core import Server as DataServer
from api._types.settings import GameSettings, ServerMetadata
from api.constants import SERVERS_DIRECTORY, AppConfig
from api.deps import get_current_user, get_session
from api.utils import sanitize_str

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from pathlib import Path

router = APIRouter()

LOG_TAIL_BYTES = 200_000

# Factorio matchmaking endpoint listing all currently public games.
MATCHMAKING_URL = "https://multiplayer.factorio.com/get-games"

# Headers that keep Server-Sent-Events flowing through proxies/uvicorn without
# buffering or caching.
SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


async def fetch_public_game_names(username: str, token: str) -> set[str] | None:
    """Names of all currently-listed public Factorio games, or None on failure.

    One matchmaking call returns the whole global list, so callers can fetch it
    once and match many servers against it.
    """
    if not username or not token:
        return None
    try:
        async with httpxyz.AsyncClient(timeout=10.0) as client:
            resp = await client.get(MATCHMAKING_URL, params={"username": username, "token": token})
            resp.raise_for_status()
            games = resp.json()
    except Exception:  # noqa: BLE001 - any failure means we just can't tell
        return None
    if not isinstance(games, list):
        return None
    return {g["name"] for g in games if isinstance(g, dict) and isinstance(g.get("name"), str)}


def _get_server_or_404(user: User, name: str) -> DataServer:
    server = user.servers.get(name) if getattr(user, "servers", None) else None
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


def _read_log_tail(log_path: Path, limit: int = LOG_TAIL_BYTES) -> str:
    """Return the tail of a log file while keeping huge files manageable."""
    if not log_path.exists():
        return ""
    data = log_path.read_text(encoding="utf-8", errors="replace")
    if limit and len(data) > limit:
        return data[-limit:]
    return data


def _safe_version(server: DataServer) -> str | None:
    try:
        return server.factorio_version
    except AttributeError:
        return None


def _load_settings(server: DataServer) -> GameSettings:
    if server.files.server_settings.exists():
        return GameSettings.read(server.files.server_settings)
    return GameSettings(name=server.name)


def _load_meta(server: DataServer) -> ServerMetadata:
    if server.files.manager_meta.exists():
        return ServerMetadata.read(server.files.manager_meta)
    return ServerMetadata()


class PublicDisplayPayload(BaseModel):
    """Manager metadata: opt-in public display and which fields are exposed."""

    public_display: bool | None = None
    show_name: bool | None = None
    show_status: bool | None = None
    show_reachability: bool | None = None
    show_ip: bool | None = None


class SettingsPayload(BaseModel):
    """Partial server-settings update; only provided fields are applied.

    Mirrors the Factorio 2.1 server-settings.json fields. ``visibility`` is split
    into the flat ``visibility_public`` / ``visibility_lan`` for convenience.
    """

    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    game_password: str | None = None
    max_players: int | None = Field(default=None, ge=0)
    visibility_public: bool | None = None
    visibility_lan: bool | None = None
    username: str | None = None
    token: str | None = None
    require_user_verification: bool | None = None
    max_upload_in_kilobytes_per_second: int | None = Field(default=None, ge=0)
    max_upload_slots: int | None = Field(default=None, ge=0)
    minimum_latency_in_ticks: int | None = Field(default=None, ge=0)
    max_heartbeats_per_second: int | None = Field(default=None, ge=6, le=240)
    ignore_player_limit_for_returning_players: bool | None = None
    allow_commands: str | None = None
    autosave_interval: int | None = Field(default=None, ge=0)
    autosave_slots: int | None = Field(default=None, ge=0)
    afk_autokick_interval: int | None = Field(default=None, ge=0)
    auto_pause: bool | None = None
    auto_pause_when_players_connect: bool | None = None
    only_admins_can_pause_the_game: bool | None = None
    autosave_only_on_server: bool | None = None
    non_blocking_saving: bool | None = None
    # Manager metadata (persisted separately from Factorio server-settings.json).
    public_display: PublicDisplayPayload | None = None


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


@router.get("/server/{name}/settings")
async def get_settings(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Return the current server settings as JSON."""
    server = _get_server_or_404(current_user, name)
    return {**asdict(_load_settings(server)), "public_display": asdict(_load_meta(server))}


@router.patch("/server/{name}/settings")
async def update_settings(
    name: str,
    payload: SettingsPayload,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Update (partially) the server settings and persist them."""
    server = _get_server_or_404(current_user, name)
    settings = _load_settings(server)
    provided = payload.model_dump(exclude_unset=True)

    # Manager metadata is stored separately from Factorio's server-settings.json.
    meta_provided = provided.pop("public_display", None)
    if meta_provided is not None:
        meta = _load_meta(server)
        for field_name, value in meta_provided.items():
            if value is not None:
                setattr(meta, field_name, value)
        meta.write(server.files.manager_meta)

    if "visibility_public" in provided:
        settings.visibility.public = provided.pop("visibility_public")
    if "visibility_lan" in provided:
        settings.visibility.lan = provided.pop("visibility_lan")
    for field_name, value in provided.items():
        setattr(settings, field_name, value)
    server.settings.game = settings
    settings.write(server.files.server_settings)
    return {**asdict(settings), "public_display": asdict(_load_meta(server))}


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
        await server.remove()
    except Exception as err:
        # best-effort removal
        raise HTTPException(status_code=500, detail="Failed to remove server") from err
    return JSONResponse(status_code=204, content={})


@router.get("/server/{name}/logs")
async def get_logs(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Return current and previous logs (tail-limited) for the named server."""
    server = _get_server_or_404(current_user, name)
    return {
        "current_log": _read_log_tail(server.files.current_log),
        "previous_log": _read_log_tail(server.files.previous_log),
    }


@router.get("/server/{name}/logs/stream")
async def logs_stream(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """Live-tail the current log file as a Server-Sent-Events stream."""
    server = _get_server_or_404(current_user, name)
    log_path = server.files.current_log

    async def generate() -> AsyncGenerator[str]:
        # Start from the end of the file; the frontend seeds its own backlog via
        # the one-shot /logs endpoint, so here we only emit newly appended lines.
        last_size = log_path.stat().st_size if log_path.exists() else 0
        while True:
            try:
                if not log_path.exists():
                    await asyncio.sleep(1.0)
                    continue
                size = log_path.stat().st_size
                if size < last_size:
                    # File was rotated/truncated; re-read from the start.
                    last_size = 0
                if size > last_size:
                    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
                        handle.seek(last_size)
                        chunk = handle.read()
                        last_size = handle.tell()
                    for line in chunk.splitlines():
                        yield f"data: {line}\n\n"
                else:
                    await asyncio.sleep(0.5)
            except OSError:
                await asyncio.sleep(1.0)

    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)


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
        raise HTTPException(status_code=502, detail=str(err)) from err
    return {"response": response}


@router.get("/server/{name}/reachable")
async def reachable(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Report whether the server is actually publicly discoverable.

    Authoritative check: query Factorio's matchmaking list and see whether this
    server (by name) appears among the currently-listed public games.
    """
    server = _get_server_or_404(current_user, name)
    settings = _load_settings(server)

    if not settings.visibility.public:
        return {"discoverable": False, "reason": "Server visibility is not set to public"}
    if not settings.username or not settings.token:
        return {"discoverable": False, "reason": "No Factorio account credentials configured"}

    names = await fetch_public_game_names(settings.username, settings.token)
    if names is None:
        return {"discoverable": None, "reason": "Could not reach the Factorio matchmaking service"}

    target = settings.name or server.name
    listed = target in names
    return {
        "discoverable": listed,
        "reason": None if listed else "Server is not listed in the public game browser",
    }


@router.get("/servers/public")
async def public_servers(db: Annotated[Session, Depends(get_session)]) -> dict:
    """List opt-in public servers across all users. No authentication required.

    Each server exposes only the fields its owner enabled; owner identity is
    never returned.
    """
    entries: list[tuple[DataServer, ServerMetadata, GameSettings]] = []
    if SERVERS_DIRECTORY.exists():
        for user_dir in SERVERS_DIRECTORY.iterdir():
            if not user_dir.is_dir() or not user_dir.name.isdigit():
                continue
            user = db.get(User, int(user_dir.name))
            if user is None:
                continue
            for server in user.servers.values():
                meta = _load_meta(server)
                if meta.public_display:
                    entries.append((server, meta, _load_settings(server)))

    # One matchmaking fetch covers every server: use the first available creds.
    names: set[str] | None = None
    for _server, _meta, settings in entries:
        if settings.username and settings.token:
            names = await fetch_public_game_names(settings.username, settings.token)
            break

    result: list[dict] = []
    for server, meta, settings in entries:
        status: str | None = None
        if meta.show_status:
            try:
                status = server.status
            except (AttributeError, OSError):
                status = None
        address: str | None = None
        if meta.show_ip:
            try:
                address = f"{server.ip}:{server.port}"
            except (AttributeError, OSError, ValueError):
                address = None
        reachable: bool | None = None
        if meta.show_reachability and names is not None:
            reachable = (settings.name or server.name) in names
        result.append(
            {
                "name": (settings.name or server.name) if meta.show_name else None,
                "status": status,
                "address": address,
                "reachable": reachable,
            },
        )

    return {"servers": result}


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
