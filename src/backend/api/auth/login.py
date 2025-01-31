"""Module for handling user login."""

from typing import Any

import aiohttp
from fastapi import APIRouter, Request

from backend.constants import API_VERSION, LOGIN_API, REQUIRE_GAME_OWNERSHIP


aio_http_session = aiohttp.ClientSession()

router = APIRouter()

@router.get("/login")
async def login(request: Request) -> dict[Any, Any]:
    """Log in the user with the given username and password."""
    print(f"{request}")
    username: str = request.get("username", None)
    password: str = request.get("password", None)
    auth_code: str | None = request.get("auth_code", None)
    return await get_auth_token(username, password, auth_code)


async def get_auth_token(
        username_or_email: str,
        password: str,
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
        data = {
            "username": username_or_email,
            "password": password,
            "api_version": API_VERSION,
            "require_game_ownership": REQUIRE_GAME_OWNERSHIP,
            "email_authentication_code": email_authentication_code,
        }
        async with aio_http_session.post(LOGIN_API, data=data, timeout=5) as resp:
            return await resp.json()
