"""Main FastAPI application."""

from datetime import UTC, datetime, timedelta

import fastapi
import jwt
from api import router as api_router
from constants import ENCODING_ALGORITHM, JWT_EXPIRATION, SECRET_KEY
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from models.user import User


app = fastapi.FastAPI()
app.include_router(api_router)


oath2 = OAuth2PasswordBearer(tokenUrl="token")
origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_access_token(data: User, expires_delta: timedelta | None = None) -> str:
    """Create a new access token."""
    to_encode = data.model_dump().copy()
    expire = datetime.now(UTC) + expires_delta if expires_delta else datetime.now(UTC) + timedelta(minutes=JWT_EXPIRATION)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ENCODING_ALGORITHM)


def validate_access_token(token: str) -> User | dict[str, str]:
    """Validate the given access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ENCODING_ALGORITHM])
        user = User(**payload)
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired."}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token."}
    else:
        return user
