"""Contains models for the auth module."""

from pydantic import BaseModel, SecretStr


class LoginForm(BaseModel):
    """Form for logging in a user."""
    username: str
    password: SecretStr
    auth_code: str | None = None

class FactorioLoginSchema(BaseModel):
    """Form for logging in a user on factorio's end."""
    content: str = "application/x-www-form-urlencoded"

    username: str
    password: SecretStr
    api_version: int
    require_game_ownership: bool
    email_authentication_code: str | None = None

