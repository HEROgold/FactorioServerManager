"""Current-user API router (used by the React UserContext)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api._types.database import User
from api.deps import get_current_user

router = APIRouter()


class CurrentUser(BaseModel):
    """Authenticated user information returned to the frontend."""

    id: int
    email: str | None
    display_name: str
    has_factorio_token: bool


@router.get("/me")
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> CurrentUser:
    """Return the currently authenticated user."""
    return CurrentUser(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        has_factorio_token=current_user.factorio_token is not None,
    )
