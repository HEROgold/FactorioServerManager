"""The module where some app level routes are defined."""

from typing import Literal

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

import blueprints  # type: ignore[no-stub-file]
from _types import Website, User, FactorioInterface, get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

app = Website(__name__)

for bp in blueprints.all_blueprints:
    app.register_blueprint(bp)

@router.get("/dashboard", response_class=HTMLResponse)
async def index(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard/index.html", {"request": request, "servers": current_user.servers.values()})

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    user = User.fetch_by_email(email)
    fi = FactorioInterface()
    user.fi = fi

    resp = await user.fi.get_auth_token(email, password)
    if resp:
        token = resp.get("token")
        if not token:
            raise HTTPException(status_code=400, detail="Login failed")
        user.factorio_token = token
        # Implement session management
        return RedirectResponse(url="/dashboard", status_code=303)
    raise HTTPException(status_code=400, detail="Login failed")

@app.errorhandler(404)
async def page_not_found(e: Exception) -> tuple[str, Literal[404]]:
    """Handle 404 errors."""
    return templates.TemplateResponse("404.j2", {"request": request, "error": e}), 404

@app.errorhandler(KeyError)
async def key_error(_: Exception) -> tuple[Response, Literal[404]]:
    """Handle KeyErrors errors."""
    return RedirectResponse(url=request.endpoint or "/"), 404
