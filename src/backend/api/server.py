"""Server API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.models.user import User


async def get_current_user() -> User:
    """Get the current user."""
    return await User.from_token("token")


router = APIRouter(prefix="/server", tags=["server"])


@router.get("/list")
async def list_servers(user: Annotated[User, Depends(get_current_user)]) -> list[str]:
    """List all servers that the user has access to."""
    return await user.get_servers()
