from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from FSM._types.database import User
from ..deps import get_current_user

router = APIRouter(prefix="/dashboard")

templates_dir = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/", response_class=templates.TemplateResponse)
async def index(request: Request, current_user: User = Depends(get_current_user)):
    """Render the server overview for the current user."""
    servers = list(current_user.servers.values()) if getattr(current_user, "servers", None) else []
    return templates.TemplateResponse("server/overview.j2", {"request": request, "servers": servers, "user": current_user})
