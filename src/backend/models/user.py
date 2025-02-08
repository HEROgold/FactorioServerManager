"""Model for a user."""

from pydantic import BaseModel


class User(BaseModel):
    """Model for a user."""

    username: str
    email: str
    password: str
