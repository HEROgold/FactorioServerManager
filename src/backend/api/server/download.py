"""Server related download endpoints."""

from fastapi import APIRouter

from backend.core.server import Server
from backend.utils.strings import sanitize


router = APIRouter()

@router.post("/create")
async def create(name: str, version: str, port: int):
    """Create a server."""
    name = sanitize(name)

    server = Server(name, get_current_user())
    server.settings.port = port
    current_user.add_server(server)

    server = current_user.servers[name]
    await server.create(version)
    return redirect(url_for(".index", name=name))
