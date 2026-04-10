
"""Dashboard API router (returns server overview as JSON)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.deps import get_current_user

if TYPE_CHECKING:
    from fsm._types.data import Server
    from fsm._types.database import User

router = APIRouter(prefix="/dashboard")

class DashboardResponse(BaseModel):
    """Data model for dashboard response."""

    servers: list[Server]

@router.get("/")
async def index(
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardResponse:
    """Return server overview for the current user as JSON (API-only)."""
    return DashboardResponse(servers=list(current_user.servers.values()))
