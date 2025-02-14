"""Model for a user."""

from datetime import UTC, datetime, timedelta
from typing import Self

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from backend.constants import ENCODING_ALGORITHM, FREE_SERVER_LIMIT, JWT_EXPIRATION, SECRET_KEY
from backend.core.server import Server


oath2 = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    """Model for a user."""

    id: int
    username: str
    email: str
    password: str
    servers: dict[str, Server] = {}

    async def get_servers(self) -> list[str]:
        """Get the servers that the user has."""
        return ["server1", "server2"]

    @staticmethod
    async def from_token(token: str) -> Self:
        """Get a user from a token."""
        return await decrypt_token(token)

    def can_add_server(self) -> bool:
        """Check if the user can add a server."""
        return not len(self.servers) >= FREE_SERVER_LIMIT

    def is_server_registered(self, server: Server) -> bool:
        """Check if the server is registered to the user."""
        return bool(self.servers[server.name] or server.exists)

    def add_server(self, server: Server) -> None:
        """Add a server to the user."""
        self.servers[server.name] = server


async def create_access_token(data: User, expires_delta: timedelta | None = None) -> str:
    """Create a new access token."""
    to_encode = data.model_dump().copy()
    expire = datetime.now(UTC) + expires_delta if expires_delta else datetime.now(UTC) + timedelta(minutes=JWT_EXPIRATION)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ENCODING_ALGORITHM)


async def decrypt_token(token: str) -> User:
    """Decrypt the given token."""
    return User(**jwt.decode(token, SECRET_KEY, algorithms=[ENCODING_ALGORITHM]))


async def validate_access_token(token: str) -> User | dict[str, str]:
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


async def get_current_user(token: str = Depends(oath2)) -> User:
    """Get the current user."""
    return await User.from_token(token)
