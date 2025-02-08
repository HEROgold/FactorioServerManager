"""Server API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends


# TODO @HEROgold: move this class to a separate file
# 0
class User:
    """Class Representing a User."""

    async def get_servers(self) -> list[str]:
        """Get the servers that the user has access to."""
        return ["server1", "server2"]


async def get_current_user() -> User:
    """Get the current user."""
    return User()


router = APIRouter(prefix="/server", tags=["server"])


@router.get("/list")
async def list_servers(user: Annotated[User, Depends(get_current_user)]) -> list[str]:
    """List all servers that the user has access to."""
    return await user.get_servers()
