"""Shared helpers used across the split server routers.

Kept separate (rather than duplicated or imported from one of the endpoint
modules) to avoid circular imports between ``server_lifecycle``,
``server_settings``, ``server_logs``, ``server_rcon`` and ``server_public``.
"""

from __future__ import annotations

from logging import getLogger

import httpxyz

from api._types.database import User
from api._types.server.core import Server as DataServer
from api._types.settings import GameSettings, ServerMetadata
from fastapi import HTTPException

logger = getLogger(__name__)

# Factorio matchmaking endpoint listing all currently public games.
MATCHMAKING_URL = "https://multiplayer.factorio.com/get-games"


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
    except (httpxyz.HTTPError, ValueError) as exc:
        logger.debug("Matchmaking lookup failed: %s", exc)
        return None
    if not isinstance(games, list):
        return None
    return {g["name"] for g in games if isinstance(g, dict) and isinstance(g.get("name"), str)}


def _get_server_or_404(user: User, name: str) -> DataServer:
    server = user.servers.get(name) if getattr(user, "servers", None) else None
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


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
