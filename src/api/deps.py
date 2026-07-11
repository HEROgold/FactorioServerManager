"""Dependency helpers for API routers.

Includes session token creation and current-user resolution helpers.
"""

import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from api import constants
from api._types.database import User, engine
from api.config import app_config, session_config

if TYPE_CHECKING:
    from collections.abc import Generator

    from fastapi import Response

# Name of the non-HttpOnly cookie used for double-submit CSRF protection. It is
# readable by the SPA, which echoes it back in the ``X-CSRF-Token`` header; the
# CSRF middleware rejects any state-changing request whose header does not match.
CSRF_COOKIE_NAME = "fsm_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"


def _is_production() -> bool:
    return app_config.environment.strip().strip('"').lower() == "production"

# Placeholder that must never be used to sign real sessions: it is the committed
# default and is publicly known, so any token signed with it is forgeable.
_INSECURE_SECRET = "secret"  # noqa: S105


def _resolve_session_secret() -> str:
    """Resolve the secret used to sign session JWTs, failing closed on weak values.

    Precedence: the ``FSM_SECRET_KEY`` environment variable, then a non-default
    ``secret`` from ``api_config.ini``. The publicly-known placeholder
    ``"secret"`` is always rejected so a forgeable default can never reach
    production. In production a strong secret must be provided explicitly;
    other environments fall back to the persisted, randomly-generated key file
    (:data:`api.constants.SECRET_KEY`) for developer convenience.
    """
    candidates = (
        (os.getenv(constants.SECRET_KEY_ENV) or "").strip(),
        (session_config.secret or "").strip(),
    )
    for candidate in candidates:
        if candidate and candidate != _INSECURE_SECRET:
            return candidate

    if _is_production():
        msg = (
            "No secure session secret configured. Set the "
            f"{constants.SECRET_KEY_ENV} environment variable to a random value, "
            'e.g. `python -c "import secrets; print(secrets.token_hex(64))"`.'
        )
        raise RuntimeError(msg)

    # Development fallback: a strong, persisted random key (never the placeholder).
    return constants.SECRET_KEY


# Resolved once at import so a misconfigured production deployment fails fast at
# startup rather than silently signing forgeable sessions.
SESSION_SECRET = _resolve_session_secret()


def set_session_cookies(response: Response, user_id: int) -> None:
    """Attach the session and CSRF cookies for ``user_id`` to ``response``.

    The session cookie is HttpOnly (unreadable by JS); the CSRF cookie is
    readable so the SPA can echo it in the ``X-CSRF-Token`` header. Both are
    marked ``Secure`` in production so they never travel over plaintext.
    """
    secure = _is_production()
    session_token = create_session_token(user_id)
    response.set_cookie(
        session_config.cookie_name,
        session_token,
        httponly=True,
        samesite="lax",
        secure=secure,
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        secrets.token_urlsafe(32),
        httponly=False,
        samesite="lax",
        secure=secure,
    )


def clear_session_cookies(response: Response) -> None:
    """Delete the session and CSRF cookies from ``response``."""
    response.delete_cookie(session_config.cookie_name)
    response.delete_cookie(CSRF_COOKIE_NAME)


def get_session() -> Generator[Session]:
    """Yield a database session bound to the SQLite engine for the request."""
    with Session(engine) as session:
        yield session


def create_session_token(user_id: int, expires_minutes: int = 60) -> str:
    """Create a signed session token for the given user id.

    The token `exp` claim is timezone-aware (UTC).
    """
    exp = datetime.now(tz=UTC) + timedelta(minutes=expires_minutes)
    payload = {"sub": str(user_id), "exp": exp}
    return jwt.encode(payload, SESSION_SECRET, algorithm=session_config.algorithm)


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_session)],
) -> User:
    """Resolve the current user from the session cookie and DB session.

    Raises an HTTP 401 when the session is missing or invalid.
    """
    token = request.cookies.get(session_config.cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        data = jwt.decode(token, SESSION_SECRET, algorithms=[session_config.algorithm])
    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        ) from err

    sub = data.get("sub")
    if not isinstance(sub, str) or not sub.lstrip("-").isdigit():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )
    uid = int(sub)

    user = db.get(User, uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user
