"""Pydantic models for request/response validation."""

from pydantic import BaseModel, EmailStr, Field, field_validator


# Authentication models
class LoginRequest(BaseModel):
    """Login request with Factorio credentials."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    display_name: str


class User(BaseModel):
    """User model."""
    id: int
    email: str
    display_name: str

    class Config:
        """Pydantic config."""
        from_attributes = True


# Server models
class ServerCreate(BaseModel):
    """Server creation request."""
    name: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate server name."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Server name must contain only alphanumeric characters, hyphens, and underscores")
        return v


class ServerUpdate(BaseModel):
    """Server update request."""
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")


class ServerSettings(BaseModel):
    """Server settings update."""
    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    max_players: int | None = Field(None, ge=0, le=65535)
    visibility: dict | None = None
    username: str | None = None
    password: str | None = None
    token: str | None = None
    game_password: str | None = None
    require_user_verification: bool | None = None
    max_upload_in_kilobytes_per_second: int | None = None
    max_upload_slots: int | None = None
    minimum_latency_in_ticks: int | None = None
    ignore_player_limit_for_returning_players: bool | None = None
    allow_commands: str | None = None
    autosave_interval: int | None = None
    autosave_slots: int | None = None
    afk_autokick_interval: int | None = None
    auto_pause: bool | None = None
    only_admins_can_pause_the_game: bool | None = None
    autosave_only_on_server: bool | None = None


class ServerInfo(BaseModel):
    """Server information response."""
    name: str
    status: str
    version: str | None = None
    port: int | None = None
    ip: str | None = None

    class Config:
        """Pydantic config."""
        from_attributes = True


class ServerStatus(BaseModel):
    """Server status response."""
    status: str
    container_id: str | None = None


# Mod models
class ModSearchParams(BaseModel):
    """Mod search parameters."""
    query: str = ""
    page: int = Field(1, ge=1)
    page_size: int = Field(12, ge=1, le=100)


class ModInstallRequest(BaseModel):
    """Mod installation request."""
    mod_name: str
    version: str | None = None


class ModBatchInstallRequest(BaseModel):
    """Batch mod installation request."""
    mods: list[ModInstallRequest]


class ModToggleRequest(BaseModel):
    """Mod enable/disable request."""
    mod_name: str
    enabled: bool


class ModEntry(BaseModel):
    """Mod list entry."""
    name: str
    enabled: bool
    version: str | None = None


class ModListResponse(BaseModel):
    """Mod list response."""
    mods: list[ModEntry]


# Rate limiting models
class RateLimitError(BaseModel):
    """Rate limit error response."""
    detail: str
    retry_after: int  # seconds
