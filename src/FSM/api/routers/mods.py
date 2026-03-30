from pathlib import Path
import json

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from FSM._types.database import User
from ..deps import get_current_user
from ..db import get_session

router = APIRouter(prefix="/server/{name}/mods")

templates_dir = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.post("/install", response_class=HTMLResponse)
async def install(request: Request, name: str, mod_name: str = Form(...), version: str = Form(...), current_user: User = Depends(get_current_user)):
    server = current_user.servers.get(name) if getattr(current_user, "servers", None) else None
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    if not mod_name or not version:
        raise HTTPException(status_code=400, detail="Missing mod name or version")
    factorio_token = getattr(current_user, "factorio_token", None)
    if not factorio_token:
        return HTMLResponse("Factorio login required before downloading mods.", status_code=400)
    try:
        mod_payload = await current_user.fi.get_mod_full(mod_name)
    except Exception:
        raise HTTPException(status_code=502, detail="Unable to reach Factorio mod portal")
    release = next((r for r in mod_payload.get("releases", []) if r.get("version") == version), None)
    if not release:
        raise HTTPException(status_code=404, detail="Requested mod version not found")

    # Perform download and install using existing FactorioInterface + server helpers
    try:
        await current_user.fi.download_mod_release(release, server.path)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to download or install mod")

    # Update server internal state (existing code manages persisted files)
    server.upsert_mod_entry(mod_name, enabled=True, version=version)

    template = templates.TemplateResponse("server/mods/_installed_list.j2", {"request": request, "server": server, "installed_mods": server.describe_mods()})
    template.headers["HX-Trigger"] = json.dumps({"mods-changed": {"name": mod_name, "action": "installed"}})
    return template
