"""Model for a user."""

from typing import Self

from pydantic import BaseModel


class User(BaseModel):
    """Model for a user."""

    username: str
    email: str
    password: str

    async def get_servers(self) -> list[str]:
        """Get the servers that the user has."""
        return ["server1", "server2"]

    @staticmethod
    async def from_token(token: str) -> Self:
        """Get a user from a token."""
