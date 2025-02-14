"""Module for handling user login."""

from typing import Any

import httpx
from fastapi import APIRouter
from pydantic import SecretStr

from backend.constants import API_VERSION, LOGIN_API, REQUIRE_GAME_OWNERSHIP
from backend.models.login import FactorioLoginSchema, LoginForm
from backend.models.user import User, get_current_user


router = APIRouter(prefix="/auth")


@router.post("/login")
async def login(login: LoginForm) -> dict[Any, Any]:
    """Log in the user with the given username and password."""
    return await get_auth_token(
        login.username,
        login.password,
        login.auth_code,
    )


@router.post("/validate")
async def validate(token: str) -> bool:
    """Validate the user's token."""
    return User.from_token(token) == get_current_user()


async def get_auth_token(
    username_or_email: str,
    password: SecretStr,
    email_authentication_code: str | None = None,
) -> dict[Any, Any]:
    """Log in the user with the given username and password, and optionally an email code.

    Parameters
    ----------
    username_or_email: :class:`str`
        the username or the email for the login
    password: :class:`str`
        the password for logging in
    email_authentication_code: :class:`str`
        the email authentication code that might be required for logging in

    """
    data = FactorioLoginSchema(
        username=username_or_email,
        password=password,
        api_version=API_VERSION,
        require_game_ownership=REQUIRE_GAME_OWNERSHIP,
        email_authentication_code=email_authentication_code,
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(
            LOGIN_API,
            data=data.model_dump(),
            timeout=5.0,
        )
        return response.json()
