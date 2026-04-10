"""Dependency helpers for API routers.

Includes session token creation and current-user resolution helpers.
"""

import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException, Request, status
from herogold.orm.constants import session
from jose import JWTError, jwt

from FSM._types.database import User

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

def get_session() -> Session:
    """Get a database session for the current request."""
    return session

SECRET = os.environ.get("FSM_SECRET", "replace-me-with-env-secret")
ALGO = "HS256"
COOKIE_NAME = "fsm_session"


def create_session_token(user_id: int, expires_minutes: int = 60) -> str:
    """Create a signed session token for the given user id.

    The token `exp` claim is timezone-aware (UTC).
    """
    exp = datetime.now(tz=UTC) + timedelta(minutes=expires_minutes)
    payload = {"sub": str(user_id), "exp": exp}
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_session)],
) -> User:
    """Resolve the current user from the session cookie and DB session.

    Raises an HTTP 401 when the session is missing or invalid.
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        data = jwt.decode(token, SECRET, algorithms=[ALGO])
        sub = data.get("sub")
        try:
            uid = int(sub)
        except (TypeError, ValueError) as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session",
            ) from err
    except (JWTError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        ) from err

    user = db.get(User, uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user
