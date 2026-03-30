import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from jose import jwt, JWTError

from FSM._types.database import User
from .db import get_session

SECRET = os.environ.get("FSM_SECRET", "replace-me-with-env-secret")
ALGO = "HS256"
COOKIE_NAME = "fsm_session"


def create_session_token(user_id: int, expires_minutes: int = 60):
    payload = {"sub": str(user_id), "exp": datetime.utcnow() + timedelta(minutes=expires_minutes)}
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def get_current_user(request: Request, db=Depends(get_session)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        data = jwt.decode(token, SECRET, algorithms=[ALGO])
        uid = int(data.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
