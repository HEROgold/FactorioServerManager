"""Login/logout API endpoints (session cookie-based)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, SecretStr

from api._types.database import User
from api.constants import AppConfig
from api.deps import clear_session_cookies, set_session_cookies
from api.ratelimit import is_rate_limited

if TYPE_CHECKING:
    from api._types.factorio_interface import AuthToken

logger = logging.getLogger(__name__)

# Brute-force brake: at most this many login attempts per client IP per window.
_LOGIN_ATTEMPT_LIMIT = 10
_LOGIN_WINDOW_SECONDS = 300

router = APIRouter()


def is_email_allowed(email: str) -> bool:
    """Whether ``email`` may log in, per the configured allowlist.

    An empty allowlist admits any authenticated account (single-operator
    default); a non-empty one restricts login to the listed emails.
    """
    raw = AppConfig.AUTH_ALLOWED_EMAILS or ""
    allowed = {entry.strip().lower() for entry in raw.split(",") if entry.strip()}
    if not allowed:
        logger.warning(
            "AUTH_ALLOWED_EMAILS is empty: any Factorio account can log in. Set it "
            "to restrict the manager to known operators.",
        )
        return True
    return email.strip().lower() in allowed


class LoginForm(BaseModel):
    """Data model for login form submission."""

    email: EmailStr
    password: SecretStr
    email_auth_code: str | None = None

async def get_response(auth: AuthToken) -> JSONResponse:
    """Validate the user's Factorio token and return an appropriate response."""
    if not auth:
        return JSONResponse({"detail": "Login failed"}, status_code=400)
    if auth.email_authentication_required:
        return JSONResponse({"detail": "Email authentication required"}, status_code=400)
    if not auth.token:
        return JSONResponse({"detail": "Login failed"}, status_code=400)

    return JSONResponse({"detail": "Login successful"})

@router.post("/login")
async def login(
    form: LoginForm,
    request: Request,
) -> JSONResponse:
    """Authenticate with Factorio and create a session cookie."""
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(
        client_ip,
        limit=_LOGIN_ATTEMPT_LIMIT,
        window_seconds=_LOGIN_WINDOW_SECONDS,
        bucket="login",
    ):
        return JSONResponse(
            {"detail": "Too many login attempts. Try again later."},
            status_code=429,
        )

    if not is_email_allowed(form.email):
        return JSONResponse({"detail": "Account not permitted"}, status_code=403)

    user = User.fetch_by_email(form.email)
    auth = await user.fi.get_auth_token(
        form.email,
        form.password.get_secret_value(),
        form.email_auth_code,
    )

    response = await get_response(auth)
    token = auth.token
    if not token:
        return response

    user.persist_factorio_token(token)
    set_session_cookies(response, user.id)
    return response


@router.post("/logout")
async def logout() -> JSONResponse:
    """Drop the session cookie and return success."""
    response = JSONResponse({"detail": "logged out"})
    clear_session_cookies(response)
    return response
