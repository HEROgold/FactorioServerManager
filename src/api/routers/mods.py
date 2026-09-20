"""Mod manager API router.

Mirrors the legacy Flask mod manager blueprint, returning JSON instead of
rendered HTML. Backed by the Factorio mod portal via ``user.fi.mods``.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

import httpxyz
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api._types import mod_store
from api._types.database import User
from api.deps import get_current_user

if TYPE_CHECKING:
    from api._types.factorio_interface import Mod, ModRelease
    from api._types.server.core import Server

PORTAL_ASSET_BASE = "https://mods-data.factorio.com"
FACTORIO_VERSION_FIELD = "factorio_version"

logger = getLogger(__name__)

router = APIRouter()


def _get_server_or_404(user: User, name: str) -> Server:
    server = user.servers.get(name) if getattr(user, "servers", None) else None
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


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


def _release_info_json(release: dict[str, Any]) -> dict[str, Any]:
    return release.get("info_json", {})


def _release_factorio_version(release: dict[str, Any]) -> str | None:
    return _release_info_json(release).get(FACTORIO_VERSION_FIELD)


def _release_matches_target(release: dict[str, Any], target_line: str | None) -> bool:
    if not target_line:
        return True
    release_line = _release_factorio_version(release)
    if not release_line:
        return True
    return release_line.split(".")[:2] == target_line.split(".")[:2]


def _prepare_release(release: dict[str, Any], *, is_recommended: bool) -> dict[str, Any]:
    size_bytes = release.get("file_size")
    size_label = f"{size_bytes / 1048576:.1f} MB" if size_bytes else None
    return {
        "version": release.get("version"),
        FACTORIO_VERSION_FIELD: _release_factorio_version(release),
        "released_at": _format_release_timestamp(release.get("released_at")),
        "download_url": release.get("download_url"),
        "file_name": release.get("file_name"),
        "size_label": size_label,
        "dependencies": _release_info_json(release).get("dependencies", []),
        "is_recommended": is_recommended,
    }


async def _fetch_thumbnail(current_user: User, mod_name: str) -> str | None:
    """Best-effort thumbnail lookup: the portal's list endpoint omits it, so it
    only shows up via the per-mod detail call. A failure here just means no
    thumbnail, never a broken search."""
    try:
        detail = await current_user.fi.mods.get(mod_name)
    except (httpxyz.HTTPError, ValueError):
        return None
    return _normalize_thumbnail(detail.get("thumbnail"))


async def _attach_thumbnails(current_user: User, results: list[dict[str, Any]]) -> None:
    thumbnails = await asyncio.gather(
        *(_fetch_thumbnail(current_user, result["name"]) for result in results),
    )
    for result, thumbnail in zip(results, thumbnails, strict=True):
        result["thumbnail"] = thumbnail


def _safe_version_line(server: Server) -> str | None:
    try:
        return server.factorio_version_line
    except AttributeError:
        return None


def _version_sort_key(release: dict[str, Any]) -> tuple[int, ...]:
    """Numeric sort key so '2.10.0' sorts after '2.9.0' (not before, as a string sort would)."""
    parts: list[int] = []
    for part in str(release.get("version", "")).split("."):
        parts.append(int(part) if part.isdigit() else 0)
    return tuple(parts)


class InstallRequest(BaseModel):
    """Payload for installing a specific mod release."""

    mod_name: str
    version: str


class ToggleRequest(BaseModel):
    """Payload for enabling/disabling a mod."""

    mod_name: str
    enabled: bool = True


@router.get("/server/{name}/mods")
async def index(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Return the installed mods plus context for the mod manager UI."""
    server = _get_server_or_404(current_user, name)
    return {
        "installed_mods": server.mods.describe(),
        FACTORIO_VERSION_FIELD: _safe_version_line(server) and server.factorio_version,
        "factorio_version_line": _safe_version_line(server),
        "token_missing": current_user.factorio_token is None,
    }


@router.get("/server/{name}/mods/search")
async def search(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    q: str = "",
    page: int = 1,
) -> dict:
    """Search the Factorio mod portal."""
    server = _get_server_or_404(current_user, name)
    query = q.strip()
    page = max(page, 1)
    pagination = {"page": page, "has_prev": page > 1, "has_next": False}
    results: list[dict[str, Any]] = []
    error: str | None = None
    if query:
        try:
            payload = await current_user.fi.mods.search(
                query=query,
                page=page,
                factorio_version=_safe_version_line(server),
            )
        except httpxyz.HTTPError:
            error = "Unable to connect to the Factorio mod portal."
        else:
            pagination_info = payload.get("pagination", {}) if isinstance(payload, dict) else {}
            pagination["has_next"] = page < pagination_info.get("page_count", page)
            for item in (payload.get("results", []) if isinstance(payload, dict) else []):
                latest = item.get("latest_release", {}) or {}
                results.append({
                    "name": item.get("name"),
                    "title": item.get("title") or item.get("name"),
                    "summary": item.get("summary"),
                    "owner": item.get("owner"),
                    "downloads": item.get("downloads_count", 0),
                    "score": item.get("score", 0),
                    "thumbnail": _normalize_thumbnail(item.get("thumbnail")),
                    "latest_release": latest,
                    "compatibility": _release_factorio_version(latest),
                })
            # The portal's list endpoint never includes a thumbnail; fetch it
            # per-mod (parallel, best-effort) only for this page of results.
            if results:
                await _attach_thumbnails(current_user, results)
    return {"results": results, "query": query, "pagination": pagination, "error": error}


@router.get("/server/{name}/mods/detail/{mod_name}")
async def detail(
    name: str,
    mod_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Return mod details and compatible releases."""
    server = _get_server_or_404(current_user, name)
    error: str | None = None
    releases: list[dict[str, Any]] = []
    mod_payload: dict[str, Any] = {}
    try:
        mod_payload = dict(await current_user.fi.mods.get(mod_name))
    except (httpxyz.HTTPError, ValueError):
        error = "Unable to load mod details from the Factorio portal."
    if mod_payload:
        mod_payload["thumbnail"] = _normalize_thumbnail(mod_payload.get("thumbnail"))
        target_line = _safe_version_line(server)
        raw_releases = mod_payload.get("releases", [])
        matching = [rel for rel in raw_releases if _release_matches_target(rel, target_line)]
        # Newest first: the portal returns releases in upload order, not sorted.
        usable = sorted(matching or raw_releases, key=_version_sort_key, reverse=True)[:10]
        for idx, release in enumerate(usable):
            releases.append(_prepare_release(release, is_recommended=idx == 0 and bool(matching)))
    return {
        "mod": mod_payload,
        "releases": releases,
        "token_missing": current_user.factorio_token is None,
        "error": error,
    }


def _require_factorio_credentials(current_user: User) -> tuple[str, str]:
    """Return ``(token, username)`` or raise if the user hasn't linked a Factorio account.

    The mod portal's download endpoint requires the Factorio *account*
    username (persisted at login as ``display_name``), not the login email --
    sending the email here gets a 403 Forbidden even with a valid token.
    """
    factorio_token = current_user.factorio_token
    if not factorio_token or not current_user.display_name:
        raise HTTPException(status_code=400, detail="Factorio login required before downloading mods.")
    return factorio_token, current_user.display_name


async def _fetch_mod_payload(current_user: User, mod_name: str) -> Mod:
    """Fetch a mod's portal payload, translating portal errors into HTTP errors."""
    try:
        return await current_user.fi.mods.get(mod_name)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="Invalid mod name.") from err
    except httpxyz.HTTPError as err:
        logger.exception("Failed to fetch mod payload for %s", mod_name)
        raise HTTPException(status_code=502, detail="Unable to reach the Factorio mod portal.") from err


def _select_release(mod_payload: Mod, version: str) -> ModRelease:
    """Pick the requested release out of ``mod_payload``, validating its metadata."""
    release = next(
        (rel for rel in mod_payload.get("releases", []) if rel.get("version") == version),
        None,
    )
    if not release:
        raise HTTPException(status_code=404, detail="Requested mod version was not found.")
    if not release.get("download_url") or not release.get("file_name"):
        raise HTTPException(status_code=400, detail="Release metadata is incomplete.")
    return release


async def _ensure_mod_archive(
    current_user: User,
    mod_name: str,
    release: ModRelease,
    *,
    token: str,
    email: str,
) -> Path:
    """Download ``release`` into the shared mod store if it isn't there already."""
    file_name = release["file_name"]
    store_file = mod_store.store_path(mod_name, file_name)
    if store_file.exists():
        return store_file
    try:
        await current_user.fi.mods.download_release(
            download_url=release["download_url"],
            destination=store_file,
            username=email,
            token=token,
        )
    except ValueError as exc:
        logger.exception("Failed to download mod %s", mod_name)
        raise HTTPException(status_code=400, detail="Could not download the requested mod.") from exc
    except httpxyz.HTTPError as err:
        logger.exception("Failed to download mod archive %s (%s)", mod_name, file_name)
        raise HTTPException(status_code=502, detail="Failed to download the mod archive.") from err
    return store_file


@router.post("/server/{name}/mods/install")
async def install(
    name: str,
    body: InstallRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Download and install a specific mod release."""
    server = _get_server_or_404(current_user, name)
    factorio_token, email = _require_factorio_credentials(current_user)
    mod_payload = await _fetch_mod_payload(current_user, body.mod_name)
    release = _select_release(mod_payload, body.version)
    # Replace any version this server already had, then ensure the bytes exist in
    # the shared store exactly once before linking them into this server.
    server.mods.remove_archives(body.mod_name)
    store_file = await _ensure_mod_archive(
        current_user,
        body.mod_name,
        release,
        token=factorio_token,
        email=email,
    )
    server.mods.link_from_store(body.mod_name, store_file.name)
    server.mods.upsert(body.mod_name, enabled=True, version=body.version)
    return {"installed_mods": server.mods.describe(), "action": "installed", "name": body.mod_name}


@router.post("/server/{name}/mods/state")
async def toggle_state(
    name: str,
    body: ToggleRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Enable or disable a mod."""
    server = _get_server_or_404(current_user, name)
    server.mods.upsert(body.mod_name, enabled=body.enabled)
    action = "enabled" if body.enabled else "disabled"
    return {"installed_mods": server.mods.describe(), "action": action, "name": body.mod_name}


@router.delete("/server/{name}/mods/{mod_name}")
async def remove(
    name: str,
    mod_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Remove a mod and its archives."""
    server = _get_server_or_404(current_user, name)
    if server.mods.is_bundled(mod_name):
        raise HTTPException(status_code=400, detail="Bundled game mods cannot be removed.")
    server.mods.remove_entry(mod_name)
    server.mods.remove_archives(mod_name)
    return {"installed_mods": server.mods.describe(), "action": "removed", "name": mod_name}
