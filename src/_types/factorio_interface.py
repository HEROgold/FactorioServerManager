from typing import Self

import aiohttp
from bs4 import BeautifulSoup

from config import API_VERSION, LOGIN_API, LOGIN_URL, REQUIRE_GAME_OWNERSHIP


class FactorioInterface:
    aio_http_session: aiohttp.ClientSession

    def __init__(self) -> None:  # noqa: ANN101
        self.aio_http_session = aiohttp.ClientSession()

    async def _get_csrf_details(self: Self) -> str | None:
        """
        Get the csrf token from the login page.

        Returns
        -------
        :class:`str`
            the csrf token
        """
        async with self.aio_http_session.get(LOGIN_URL, timeout=5) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            if tag := soup.find("input", {"name": "csrf_token"}):
                return tag.get("value") # type: ignore[ReportReturnType]

            msg = "Could not find csrf token"
            raise ValueError(msg)


    async def login_user(self: Self, username_or_email: str, password: str) -> str:
        """
        Log in the user to `self.aio_http_session` with the given username and password.

        Parameters
        ----------
        username_or_email: :class:`str`
            the username or the email for the login
        password: :class:`str`
            the password for logging in
        """
        data = {
            "csrf_token": await self._get_csrf_details(),
            "username_or_email": username_or_email,
            "password": password,
        }
        async with self.aio_http_session.post(LOGIN_URL, data=data, timeout=5) as resp:
            return await resp.text()


    async def get_auth_token(
        self: Self,
        username_or_email: str,
        password: str,
        email_authentication_code: str | None = None
    ) -> dict:
        """
        Log in the user with the given username and password, and optionally an email code.

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
            "email_authentication_code": email_authentication_code
        }
        async with self.aio_http_session.post(LOGIN_API, data=data, timeout=5) as resp:
            return await resp.json()
