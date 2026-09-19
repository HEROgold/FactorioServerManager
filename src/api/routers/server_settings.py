"""Server settings API routes (read/patch server-settings.json + manager meta)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api._types.database import User
from api.deps import get_current_user
from api.routers.server_shared import _get_server_or_404, _load_meta, _load_settings

router = APIRouter()


class PublicDisplayPayload(BaseModel):
    """Manager metadata: opt-in public display and which fields are exposed."""

    public_display: bool | None = None
    show_name: bool | None = None
    show_status: bool | None = None
    show_reachability: bool | None = None
    show_ip: bool | None = None


class SettingsPayload(BaseModel):
    """Partial server-settings update; only provided fields are applied.

    Mirrors the Factorio 2.1 server-settings.json fields. ``visibility`` is split
    into the flat ``visibility_public`` / ``visibility_lan`` for convenience.
    """

    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    game_password: str | None = None
    max_players: int | None = Field(default=None, ge=0)
    visibility_public: bool | None = None
    visibility_lan: bool | None = None
    username: str | None = None
    token: str | None = None
    require_user_verification: bool | None = None
    max_upload_in_kilobytes_per_second: int | None = Field(default=None, ge=0)
    max_upload_slots: int | None = Field(default=None, ge=0)
    minimum_latency_in_ticks: int | None = Field(default=None, ge=0)
    max_heartbeats_per_second: int | None = Field(default=None, ge=6, le=240)
    ignore_player_limit_for_returning_players: bool | None = None
    allow_commands: str | None = None
    autosave_interval: int | None = Field(default=None, ge=0)
    autosave_slots: int | None = Field(default=None, ge=0)
    afk_autokick_interval: int | None = Field(default=None, ge=0)
    auto_pause: bool | None = None
    auto_pause_when_players_connect: bool | None = None
    only_admins_can_pause_the_game: bool | None = None
    autosave_only_on_server: bool | None = None
    non_blocking_saving: bool | None = None
    # Manager metadata (persisted separately from Factorio server-settings.json).
    public_display: PublicDisplayPayload | None = None


@router.get("/server/{name}/settings")
async def get_settings(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Return the current server settings as JSON."""
    server = _get_server_or_404(current_user, name)
    return {**asdict(_load_settings(server)), "public_display": asdict(_load_meta(server))}


@router.patch("/server/{name}/settings")
async def update_settings(
    name: str,
    payload: SettingsPayload,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Update (partially) the server settings and persist them."""
    server = _get_server_or_404(current_user, name)
    settings = _load_settings(server)
    provided = payload.model_dump(exclude_unset=True)

    # Manager metadata is stored separately from Factorio's server-settings.json.
    meta_provided = provided.pop("public_display", None)
    if meta_provided is not None:
        meta = _load_meta(server)
        for field_name, value in meta_provided.items():
            if value is not None:
                setattr(meta, field_name, value)
        meta.write(server.files.manager_meta)

    if "visibility_public" in provided:
        settings.visibility.public = provided.pop("visibility_public")
    if "visibility_lan" in provided:
        settings.visibility.lan = provided.pop("visibility_lan")
    for field_name, value in provided.items():
        setattr(settings, field_name, value)
    server.settings.game = settings
    settings.write(server.files.server_settings)
    return {**asdict(settings), "public_display": asdict(_load_meta(server))}
