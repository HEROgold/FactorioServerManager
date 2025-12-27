"""Blueprint powering the graphical mod manager."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

import aiohttp
from flask import Blueprint, Response, abort, make_response, render_template, request
from flask_login import current_user  # type: ignore[reportAssignmentType]

from FSM.scripts import require_login

PORTAL_ASSET_BASE = "https://mods-data.factorio.com"

if TYPE_CHECKING:
    from FSM._types.data import Server
    from FSM._types.database import User

    current_user: User


bp = Blueprint("mods", __name__, url_prefix="/server/<string:name>/mods")
bp.before_request(require_login)


def _get_server_or_404(name: str) -> Server:
    try:
        return current_user.servers[name]
    except KeyError as e:
        raise abort(404, description="Server not found") from e


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


def _prepare_release(release: dict[str, Any], *, is_recommended: bool) -> dict[str, Any]:
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


def _install_response(server: Server, trigger: dict[str, Any]) -> Response:
    html = render_template(
        "server/mods/_installed_list.j2",
        server=server,
        installed_mods=server.describe_mods(),
    )
    response = make_response(html)
    response.headers["HX-Trigger"] = json.dumps(trigger)
    return response


@bp.route("/")
async def index(name: str) -> str:
    server = _get_server_or_404(name)
    token_missing = getattr(current_user, "factorio_token", None) is None
    return render_template(
        "server/mods/mod_manager.j2",
        server=server,
        installed_mods=server.describe_mods(),
        factorio_version=server.factorio_version,
        factorio_version_line=server.factorio_version_line,
        token_missing=token_missing,
    )


@bp.get("/search")
async def search(name: str) -> str:
    server = _get_server_or_404(name)
    query = (request.args.get("q") or "").strip()
    page = max(int(request.args.get("page", 1) or 1), 1)
    pagination = {"page": page, "has_prev": page > 1, "has_next": False}
    results: list[dict[str, Any]] = []
    error: str | None = None
    if query:
        try:
            payload = await current_user.fi.search_mods(
                query=query,
                page=page,
                factorio_version=server.factorio_version_line,
            )
            pagination_info = payload.get("pagination", {})
            pagination["has_next"] = page < pagination_info.get("page_count", page)
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
                    "compatibility": item.get("latest_release", {}).get("info_json", {}).get("factorio_version"),
                }
                for item in payload.get("results", [])
            ]
        except aiohttp.ClientError:
            error = "Unable to connect to the Factorio mod portal."
    return render_template(
        "server/mods/_search_results.j2",
        server=server,
        results=results,
        query=query,
        pagination=pagination,
        error=error,
    )


@bp.get("/detail/<string:mod_name>")
async def detail(name: str, mod_name: str) -> str:
    server = _get_server_or_404(name)
    token_missing = getattr(current_user, "factorio_token", None) is None
    error: str | None = None
    releases: list[dict[str, Any]] = []
    mod_payload: dict[str, Any] = {}
    try:
        mod_payload = await current_user.fi.get_mod_full(mod_name)
    except aiohttp.ClientError:
        error = "Unable to load mod details from the Factorio portal."
    if mod_payload:
        mod_payload["thumbnail"] = _normalize_thumbnail(mod_payload.get("thumbnail"))
        target_line = server.factorio_version_line
        raw_releases = mod_payload.get("releases", [])
        matching = [rel for rel in raw_releases if _release_matches_target(rel, target_line)]
        usable = matching or raw_releases
        usable = usable[:10]
        for idx, release in enumerate(usable):
            releases.append(_prepare_release(release, is_recommended=idx == 0 and bool(matching)))
    return render_template(
        "server/mods/_detail.j2",
        server=server,
        mod=mod_payload,
        releases=releases,
        token_missing=token_missing,
        error=error,
    )


@bp.post("/install")
async def install(name: str) -> Response:
    server = _get_server_or_404(name)
    mod_name = (request.form.get("mod_name") or "").strip()
    version = (request.form.get("version") or "").strip()
    if not mod_name or not version:
        abort(400, description="Missing mod name or version")
    factorio_token = getattr(current_user, "factorio_token", None)
    if not factorio_token or not current_user.email:
        return Response("Factorio login required before downloading mods.", status=400)
    try:
        mod_payload = await current_user.fi.get_mod_full(mod_name)
    except aiohttp.ClientError:
        return Response("Unable to reach the Factorio mod portal.", status=502)
    release = next((rel for rel in mod_payload.get("releases", []) if rel.get("version") == version), None)
    if not release:
        return Response("Requested mod version was not found.", status=404)
    download_url = release.get("download_url")
    file_name = release.get("file_name")
    if not download_url or not file_name:
        return Response("Release metadata is incomplete.", status=400)
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
        return Response(str(exc), status=400)
    except aiohttp.ClientError:
        return Response("Failed to download the mod archive.", status=502)
    server.upsert_mod_entry(mod_name, enabled=True, version=version)
    return _install_response(server, {"mods-changed": {"name": mod_name, "action": "installed"}})


@bp.post("/state")
async def toggle_state(name: str) -> Response:
    server = _get_server_or_404(name)
    mod_name = (request.form.get("mod_name") or "").strip()
    if not mod_name:
        abort(400, description="Missing mod name")
    if mod_name == "base":
        return Response("The base mod cannot be disabled.", status=400)
    enabled = (request.form.get("enabled") or "true").lower() == "true"
    server.upsert_mod_entry(mod_name, enabled=enabled)
    action = "enabled" if enabled else "disabled"
    return _install_response(server, {"mods-changed": {"name": mod_name, "action": action}})


@bp.route("/<string:mod_name>", methods=["DELETE"])
async def remove(name: str, mod_name: str) -> Response:
    server = _get_server_or_404(name)
    if mod_name == "base":
        return Response("The base mod cannot be removed.", status=400)
    server.remove_mod_entry(mod_name)
    server.remove_mod_archives(mod_name)
    return _install_response(server, {"mods-changed": {"name": mod_name, "action": "removed"}})
