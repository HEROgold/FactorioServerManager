"""Dashboard API router (returns server overview as JSON)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api._types.database import User
from api.deps import get_current_user
from api.routers.server import _load_settings, fetch_public_game_names

if TYPE_CHECKING:
    from api._types.server.core import Server

router = APIRouter(prefix="/dashboard")


class ServerSummary(BaseModel):
    """Lightweight server description for the dashboard list."""

    name: str
    port: int | None = None
    status: str | None = None
    reachable: bool | None = None


class DashboardResponse(BaseModel):
    """Data model for dashboard response."""

    servers: list[ServerSummary]


def _summarize(server: Server, public_names: set[str] | None) -> ServerSummary:
    try:
        port = server.port
    except (AttributeError, OSError, ValueError):
        port = None
    try:
        status = server.status
    except (AttributeError, OSError):
        status = None
    reachable: bool | None = None
    if public_names is not None:
        settings = _load_settings(server)
        reachable = (settings.name or server.name) in public_names
    return ServerSummary(name=server.name, port=port, status=status, reachable=reachable)


@router.get("/")
async def index(
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardResponse:
    """Return server overview for the current user as JSON."""
    servers = list(current_user.servers.values())

    # One matchmaking fetch for the whole dashboard (using the user's creds).
    public_names: set[str] | None = None
    for server in servers:
        settings = _load_settings(server)
        if settings.username and settings.token:
            public_names = await fetch_public_game_names(settings.username, settings.token)
            break

    return DashboardResponse(servers=[_summarize(s, public_names) for s in servers])
