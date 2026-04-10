"""Login/logout API endpoints (session cookie-based)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeIs, runtime_checkable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, SecretStr

from api.deps import create_session_token
from fsm._types.database import User

if TYPE_CHECKING:
    from fsm._types.factorio_interface import AuthToken

router = APIRouter()


class LoginForm(BaseModel):
    """Data model for login form submission."""

    email: EmailStr
    password: SecretStr
    email_auth_code: str | None = None

@runtime_checkable
class HasToken(Protocol):
    """Protocol for a valid authentication response."""

    token: str

def has_token(auth: AuthToken) -> TypeIs[HasToken]:
    """Check if the authentication response has a token.

    When the response has a token, the login succeeded.
    """
    return isinstance(auth, HasToken) and bool(auth.token)

async def get_response(auth: AuthToken) -> JSONResponse:
    """Validate the user's Factorio token and return an appropriate response."""
    if not auth:
        return JSONResponse({"detail": "Login failed"}, status_code=400)
    if not auth.token:
        return JSONResponse({"detail": "Login failed"}, status_code=400)
    if auth.email_authentication_required:
        return JSONResponse({"detail": "Email authentication required"}, status_code=400)

    return JSONResponse({"detail": "Login successful"})

@router.post("/login")
async def login(
    form: LoginForm,
) -> JSONResponse:
    """Authenticate with Factorio and create a session cookie."""
    user = User.fetch_by_email(form.email)
    auth = await user.fi.get_auth_token(
        form.email,
        form.password.get_secret_value(),
        form.email_auth_code,
    )

    response = await get_response(auth)
    if not has_token(auth):
        return response

    user.persist_factorio_token(auth.token)
    session_token = create_session_token(user.id)
    response.set_cookie("fsm_session", session_token, httponly=True, samesite="lax")
    return response


@router.post("/logout")
async def logout() -> JSONResponse:
    """Drop the session cookie and return success."""
    response = JSONResponse({"detail": "logged out"})
    response.delete_cookie("fsm_session")
    return response
