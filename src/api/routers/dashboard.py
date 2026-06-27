"""Dashboard API router (returns server overview as JSON)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api._types.database import User
from api.deps import get_current_user

if TYPE_CHECKING:
    from api._types.data import Server

router = APIRouter(prefix="/dashboard")


class ServerSummary(BaseModel):
    """Lightweight server description for the dashboard list."""

    name: str
    port: int | None = None
    status: str | None = None


class DashboardResponse(BaseModel):
    """Data model for dashboard response."""

    servers: list[ServerSummary]


def _summarize(server: Server) -> ServerSummary:
    try:
        port = server.port
    except (AttributeError, OSError, ValueError):
        port = None
    try:
        status = server.status
    except (AttributeError, OSError):
        status = None
    return ServerSummary(name=server.name, port=port, status=status)


@router.get("/")
async def index(
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardResponse:
    """Return server overview for the current user as JSON."""
    return DashboardResponse(servers=[_summarize(s) for s in current_user.servers.values()])
