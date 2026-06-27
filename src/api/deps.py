"""Dependency helpers for API routers.

Includes session token creation and current-user resolution helpers.
"""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from api._types.database import User, engine
from api.config import session_config


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
    return jwt.encode(payload, session_config.secret, algorithm=session_config.algorithm)


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
        data = jwt.decode(token, session_config.secret, algorithms=[session_config.algorithm])
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
