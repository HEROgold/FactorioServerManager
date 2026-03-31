"""Login/logout API endpoints (session cookie-based)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse

from FSM._types import FactorioInterface
from FSM._types.database import User
from FSM.api.deps import create_session_token

router = APIRouter()


@router.post("/login")
async def login(
    email: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
) -> JSONResponse:
    """Authenticate with Factorio and create a session cookie."""
    # Reuse existing User helpers to fetch or create the user record
    user = User.fetch_by_email(email)
    # instantiate FactorioInterface from the package
    fi = FactorioInterface()
    user.fi = fi

    # Attempt to obtain a Factorio auth token (same flow as the Flask app)
    resp = await user.fi.get_auth_token(email, password)
    if not resp:
        return JSONResponse({"detail": "Login failed"}, status_code=400)
    token = resp.get("token")
    if not token:
        return JSONResponse({"detail": "Login failed"}, status_code=400)
    user.persist_factorio_token(token)

    session_token = create_session_token(user.id)
    response = JSONResponse({"detail": "ok"})
    response.set_cookie("fsm_session", session_token, httponly=True, samesite="lax")
    return response


@router.post("/logout")
async def logout() -> JSONResponse:
    """Drop the session cookie and return success."""
    response = JSONResponse({"detail": "logged out"})
    response.delete_cookie("fsm_session")
    return response
