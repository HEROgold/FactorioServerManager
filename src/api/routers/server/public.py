"""Public-facing server API routes (opt-in discoverability + directory)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api._types.database import User
from api._types.server.core import Server as DataServer
from api._types.settings import GameSettings, ServerMetadata
from api.constants import SERVERS_DIRECTORY
from api.deps import get_current_user, get_session
from api.routers.server.shared import (
    _get_server_or_404,
    _load_meta,
    _load_settings,
    fetch_public_game_names,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

router = APIRouter()


@router.get("/server/{name}/reachable")
async def reachable(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Report whether the server is actually publicly discoverable.

    Authoritative check: query Factorio's matchmaking list and see whether this
    server (by name) appears among the currently-listed public games.
    """
    server = _get_server_or_404(current_user, name)
    settings = _load_settings(server)

    if not settings.visibility.public:
        return {"discoverable": False, "reason": "Server visibility is not set to public"}
    if not settings.username or not settings.token:
        return {"discoverable": False, "reason": "No Factorio account credentials configured"}

    names = await fetch_public_game_names(settings.username, settings.token)
    if names is None:
        return {"discoverable": None, "reason": "Could not reach the Factorio matchmaking service"}

    target = settings.name or server.name
    listed = target in names
    return {
        "discoverable": listed,
        "reason": None if listed else "Server is not listed in the public game browser",
    }


def _iter_candidate_users(db: Session) -> Iterator[User]:
    """Users that own a servers directory on disk, resolved from the DB."""
    if not SERVERS_DIRECTORY.exists():
        return
    for user_dir in SERVERS_DIRECTORY.iterdir():
        if not user_dir.is_dir() or not user_dir.name.isdigit():
            continue
        user = db.get(User, int(user_dir.name))
        if user is not None:
            yield user


def _collect_public_entries(
    db: Session,
) -> list[tuple[DataServer, ServerMetadata, GameSettings]]:
    """Every server across all users that opted into public display."""
    entries: list[tuple[DataServer, ServerMetadata, GameSettings]] = []
    for user in _iter_candidate_users(db):
        for server in user.servers.values():
            meta = _load_meta(server)
            if meta.public_display:
                entries.append((server, meta, _load_settings(server)))
    return entries


async def _matchmaking_names_for(
    entries: list[tuple[DataServer, ServerMetadata, GameSettings]],
) -> set[str] | None:
    """One matchmaking fetch covers every server: use the first available creds."""
    for _server, _meta, settings in entries:
        if settings.username and settings.token:
            return await fetch_public_game_names(settings.username, settings.token)
    return None


def _safe_status(server: DataServer, meta: ServerMetadata) -> str | None:
    if not meta.show_status:
        return None
    try:
        return server.status
    except (AttributeError, OSError):
        return None


def _safe_address(server: DataServer, meta: ServerMetadata) -> str | None:
    if not meta.show_ip:
        return None
    try:
        return f"{server.ip}:{server.port}"
    except (AttributeError, OSError, ValueError):
        return None


def _describe_public_server(
    server: DataServer,
    meta: ServerMetadata,
    settings: GameSettings,
    names: set[str] | None,
) -> dict:
    reachable_flag: bool | None = None
    if meta.show_reachability and names is not None:
        reachable_flag = (settings.name or server.name) in names
    return {
        "name": (settings.name or server.name) if meta.show_name else None,
        "status": _safe_status(server, meta),
        "address": _safe_address(server, meta),
        "reachable": reachable_flag,
    }


@router.get("/servers/public")
async def public_servers(db: Annotated[Session, Depends(get_session)]) -> dict:
    """List opt-in public servers across all users. No authentication required.

    Each server exposes only the fields its owner enabled; owner identity is
    never returned.
    """
    entries = _collect_public_entries(db)
    names = await _matchmaking_names_for(entries)
    result = [_describe_public_server(server, meta, settings, names) for server, meta, settings in entries]
    return {"servers": result}
