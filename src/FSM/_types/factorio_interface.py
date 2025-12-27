from pathlib import Path
from typing import Any, Self

import aiohttp
from bs4 import BeautifulSoup

from FSM.config import (
    API_VERSION,
    LOGIN_API,
    LOGIN_URL,
    MODS_API_URL,
    AppConfig,
    HTTPConfig,
)

MOD_PORTAL_BASE = "https://mods.factorio.com"

class FactorioInterface:
    aio_http_session: aiohttp.ClientSession

    def __init__(self) -> None:
        self.aio_http_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=HTTPConfig.timeout))

    async def _get_csrf_details(self: Self) -> str | None:
        """Get the csrf token from the login page.

        Returns
        -------
        :class:`str`
            the csrf token

        """
        async with self.aio_http_session.get(LOGIN_URL) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            if tag := soup.find("input", {"name": "csrf_token"}):
                return tag.get("value") # type: ignore[ReportReturnType]

            msg = "Could not find csrf token"
            raise ValueError(msg)


    async def login_user(self: Self, username_or_email: str, password: str) -> str:
        """Log in the user to `self.aio_http_session` with the given username and password.

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
        async with self.aio_http_session.post(LOGIN_URL, data=data) as resp:
            return await resp.text()


    async def get_auth_token(
        self: Self,
        username_or_email: str,
        password: str,
        email_authentication_code: str | None = None,
    ) -> dict[str, str]:
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
            "require_game_ownership": AppConfig.REQUIRE_GAME_OWNERSHIP,
            "email_authentication_code": email_authentication_code,
        }
        async with self.aio_http_session.post(LOGIN_API, data=data) as resp:
            return await resp.json()

    async def search_mods(
        self: Self,
        *,
        query: str = "",
        page: int = 1,
        page_size: int = 12,
        factorio_version: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if query:
            params["q"] = query
        if factorio_version:
            params["version"] = factorio_version
        async with self.aio_http_session.get(MODS_API_URL, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_mod_full(self: Self, mod_name: str) -> dict[str, Any]:
        url = f"{MODS_API_URL}/{mod_name}/full"
        async with self.aio_http_session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def download_mod_release(
        self: Self,
        *,
        download_url: str,
        destination: Path,
        username: str,
        token: str,
    ) -> Path:
        if not username or not token:
            msg = "Factorio credentials required for mod downloads"
            raise ValueError(msg)
        url = download_url
        if not download_url.startswith("http"):
            url = f"{MOD_PORTAL_BASE}{download_url}"
        params = {"username": username, "token": token}
        destination.parent.mkdir(parents=True, exist_ok=True)
        async with self.aio_http_session.get(url, params=params) as resp:
            resp.raise_for_status()
            with destination.open("wb") as f:
                async for chunk in resp.content.iter_chunked(32768):
                    f.write(chunk)
        return destination
