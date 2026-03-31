
"""Dashboard API router (returns server overview as JSON)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends

from FSM.api.deps import get_current_user

if TYPE_CHECKING:
    from FSM._types.database import User

router = APIRouter(prefix="/dashboard")


@router.get("/")
async def index(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Return server overview for the current user as JSON (API-only)."""
    servers = (
        list(current_user.servers.values())
        if getattr(current_user, "servers", None)
        else []
    )
    return {
        "servers": [
            {
                "name": s.name,
                "port": s.port,
                "factorio_version": s.factorio_version,
            }
            for s in servers
        ],
        "user": {
            "id": getattr(current_user, "id", None),
            "email": getattr(current_user, "email", None),
        },
    }
