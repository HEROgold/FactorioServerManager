"""Server related download endpoints."""

from fastapi import APIRouter

from backend.core.server import Server
from backend.models.user import get_current_user
from backend.utils.strings import sanitize


router = APIRouter()

@router.post("/create")
async def create(name: str, version: str, port: int) -> None:
    """Create a server."""
    user = await get_current_user()
    name = sanitize(name)

    server = Server(name=name, user=user)
    server.settings.port = port
    user.add_server(server)

    await server.create(version)
