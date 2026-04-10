"""API routes for mod-related operations (search, install, detail)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import JSONResponse

from FSM.api.deps import get_current_user

if TYPE_CHECKING:
    from FSM._types.database import User

router = APIRouter(prefix="/server/{name}/mods")


PORTAL_ASSET_BASE = "https://mods-data.factorio.com"


def _normalize_thumbnail(path: str | None) -> str | None:
    if not path:
        return None
    if path.startswith("http"):
        return path
    return f"{PORTAL_ASSET_BASE}{path}"


def _format_release_timestamp(released_at: str | None) -> str:
    if not released_at:
        return ""
    released = released_at.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(released).strftime("%Y-%m-%d")
    except ValueError:
        return released_at[:10]


def _release_matches_target(release: dict[str, Any], target_line: str | None) -> bool:
    if not target_line:
        return True
    release_line = release.get("info_json", {}).get("factorio_version")
    if not release_line:
        return True
    return release_line.split(".")[:2] == target_line.split(".")[:2]


def _prepare_release(
    release: dict[str, Any], *, is_recommended: bool,
) -> dict[str, Any]:
    size_bytes = release.get("file_size")
    size_label = None
    if size_bytes:
        size_label = f"{size_bytes / 1048576:.1f} MB"
    return {
        "version": release.get("version"),
        "factorio_version": release.get("info_json", {}).get("factorio_version"),
        "released_at": _format_release_timestamp(release.get("released_at")),
        "download_url": release.get("download_url"),
        "file_name": release.get("file_name"),
        "size_label": size_label,
        "dependencies": release.get("info_json", {}).get("dependencies", []),
        "is_recommended": is_recommended,
    }


@router.get("/")
async def index(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    """Return installed mods and server metadata for the named server."""
    server = (
        current_user.servers.get(name)
        if getattr(current_user, "servers", None)
        else None
    )
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    token_missing = getattr(current_user, "factorio_token", None) is None
    return JSONResponse(
        {
            "server": {
                "name": server.name,
                "factorio_version": server.factorio_version,
            },
            "installed_mods": server.describe_mods(),
            "token_missing": token_missing,
        },
    )


@router.get("/search")
async def search(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    q: str | None = None,
    page: int | None = 1,
) -> JSONResponse:
    """Search the Factorio mod portal for matching mods."""
    server = (
        current_user.servers.get(name)
        if getattr(current_user, "servers", None)
        else None
    )
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    query = (q or "").strip()
    page = max(int(page or 1), 1)
    results: list[dict[str, Any]] = []
    error: str | None = None
    if query:
        try:
            payload = await current_user.fi.search_mods(
                query=query,
                page=page,
                factorio_version=server.factorio_version_line,
            )
            results = [
                {
                    "name": item.get("name"),
                    "title": item.get("title") or item.get("name"),
                    "summary": item.get("summary"),
                    "owner": item.get("owner"),
                    "downloads": item.get("downloads_count", 0),
                    "score": item.get("score", 0),
                    "thumbnail": _normalize_thumbnail(item.get("thumbnail")),
                    "latest_release": item.get("latest_release", {}),
                    "compatibility": (
                        item.get("latest_release", {})
                        .get("info_json", {})
                        .get("factorio_version")
                    ),
                }
                for item in payload.get("results", [])
            ]
        except Exception:  # noqa: BLE001 - upstream client errors
            error = "Unable to connect to the Factorio mod portal."
    return JSONResponse(
        {
            "results": results,
            "query": query,
            "error": error,
            "page": page,
        },
    )


@router.get("/detail/{mod_name}")
async def detail(
    name: str,
    mod_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    """Return detail for a specific mod from the Factorio portal."""
    server = (
        current_user.servers.get(name)
        if getattr(current_user, "servers", None)
        else None
    )
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    token_missing = getattr(current_user, "factorio_token", None) is None
    error: str | None = None
    releases: list[dict[str, Any]] = []
    mod_payload: dict[str, Any] = {}
    try:
        mod_payload = await current_user.fi.get_mod_full(mod_name)
    except Exception:  # noqa: BLE001 - upstream client errors
        error = "Unable to load mod details from the Factorio portal."
    if mod_payload:
        mod_payload["thumbnail"] = _normalize_thumbnail(mod_payload.get("thumbnail"))
        target_line = server.factorio_version_line
        raw_releases = mod_payload.get("releases", [])
        matching = [
            rel
            for rel in raw_releases
            if _release_matches_target(rel, target_line)
        ]
        usable = matching or raw_releases
        usable = usable[:10]
        for idx, release in enumerate(usable):
            releases.append(
                _prepare_release(
                    release,
                    is_recommended=(idx == 0 and bool(matching)),
                ),
            )
    return JSONResponse(
        {
            "mod": mod_payload,
            "releases": releases,
            "token_missing": token_missing,
            "error": error,
        },
    )


@router.post("/install")
async def install(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    mod_name: Annotated[str, Form(...)],
    version: Annotated[str, Form(...)],
) -> JSONResponse:
    """Install a mod release for the named server."""
    server = (
        current_user.servers.get(name)
        if getattr(current_user, "servers", None)
        else None
    )
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    if not mod_name or not version:
        raise HTTPException(status_code=400, detail="Missing mod name or version")
    factorio_token = getattr(current_user, "factorio_token", None)
    if not factorio_token or not current_user.email:
        raise HTTPException(
            status_code=400,
            detail="Factorio login required before downloading mods.",
        )
    try:
        mod_payload = await current_user.fi.get_mod_full(mod_name)
    except Exception as err:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach the Factorio mod portal",
        ) from err

    releases_list = mod_payload.get("releases", [])
    release = next(
        (rel for rel in releases_list if rel.get("version") == version),
        None,
    )
    if not release:
        raise HTTPException(
            status_code=404,
            detail="Requested mod version was not found",
        )
    download_url = release.get("download_url")
    file_name = release.get("file_name")
    if not download_url or not file_name:
        raise HTTPException(
            status_code=400,
            detail="Release metadata is incomplete.",
        )
    destination = server.mods / file_name
    server.remove_mod_archives(mod_name)
    try:
        await current_user.fi.download_mod_release(
            download_url=download_url,
            destination=destination,
            username=current_user.email,
            token=factorio_token,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as err:
        raise HTTPException(
            status_code=502,
            detail="Failed to download the mod archive.",
        ) from err
    server.upsert_mod_entry(mod_name, enabled=True, version=version)
    return JSONResponse(
        {"detail": "installed", "installed_mods": server.describe_mods()},
    )


@router.post("/state")
async def toggle_state(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    mod_name: Annotated[str, Form(...)],
    enabled: Annotated[str, Form("true")],
) -> JSONResponse:
    """Toggle the enabled state for a mod on the server."""
    server = (
        current_user.servers.get(name)
        if getattr(current_user, "servers", None)
        else None
    )
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    mod_name = (mod_name or "").strip()
    if not mod_name:
        raise HTTPException(status_code=400, detail="Missing mod name")
    if mod_name == "base":
        raise HTTPException(status_code=400, detail="The base mod cannot be disabled.")
    is_enabled = (enabled or "true").lower() == "true"
    server.upsert_mod_entry(mod_name, enabled=is_enabled)
    action = "enabled" if is_enabled else "disabled"
    return JSONResponse(
        {"detail": "ok", "action": action, "installed_mods": server.describe_mods()},
    )


@router.delete("/{mod_name}")
async def remove(
    name: str,
    mod_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    """Remove a mod and its archives from the server."""
    server = (
        current_user.servers.get(name)
        if getattr(current_user, "servers", None)
        else None
    )
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    if mod_name == "base":
        raise HTTPException(status_code=400, detail="The base mod cannot be removed.")
    server.remove_mod_entry(mod_name)
    server.remove_mod_archives(mod_name)
    return JSONResponse({"detail": "removed", "installed_mods": server.describe_mods()})
