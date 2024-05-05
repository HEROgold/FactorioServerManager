from collections.abc import AsyncGenerator
from http.client import InvalidURL
from typing import TYPE_CHECKING, Self

import aiofile
import aiohttp
from bs4 import BeautifulSoup

from _types.enums import Build, Distro
from config import API_VERSION, ARCHIVE_URL, DOWNLOADS_DIRECTORY, LOGIN_API, LOGIN_URL, RELEASES_URL, REQUIRE_GAME_OWNERSHIP


if TYPE_CHECKING:
    from pathlib import Path


class FactorioInterface:
    aio_http_session: aiohttp.ClientSession

    def __init__(self: Self) -> None:
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


    async def is_downloadable(self: Self, url: str) -> bool:
        """Is the url a downloadable resource."""
        return True # Windows64 alpha is does not return True, when it should
        async with self.aio_http_session.head(url, allow_redirects=True) as h:
            header = h.headers
            content_type = header.get("content-type") or header.get("Content-Type")

            # fmt: off
            if (
                content_type is None
                or "text" in content_type.lower()
                or "html" in content_type.lower()
            ):
                return False
            return True
            # fmt: on


    async def download_server_files(  # noqa: PLR0913
        self: Self,
        build: Build,
        distro: Distro,
        version: str = "latest",
        *,
        overwrite: bool = False,
        experimental: bool = False,
    ) -> None:
        """
        Download the files for the server with the given version, build and distro.

        Parameters
        ----------
        version: :class:`str`
            The version to download
        build: :class:`str`
            The build to download
        distro: :class:`str`
            The distro to download
        overwrite: :class:`bool`
            Whether to overwrite the file if it already exists
        experimental: :class:`bool`
            Whether to download the experimental version when possible

        Raises
        ------
        :class:`ValueError`
            If any values are invalid
        """
        if version == "latest":
            versions = await self.get_versions()
            version = versions["experimental"][build.name] if experimental else versions["stable"][build.name]

        DOWNLOADS_DIRECTORY.mkdir(exist_ok=True)

        file_path = DOWNLOADS_DIRECTORY/f"{version}-{build.name}-{distro.name}"
        url = f"https://www.factorio.com/get-download/{version}/{build.name}/{distro.name}"

        if file_path.exists() and not overwrite:
            msg = f"The file already exists {file_path=}"
            raise FileExistsError(msg)

        if not await self.is_downloadable(url):
            msg = f"The url does not point to a downloadable resource: {url=}"
            raise InvalidURL(msg)

        # see https://proxiesapi.com/articles/downloading-files-in-python-with-aiohttp#:~:text=total_size%20%3D%20int(response,downloaded%7D%2F%7Btotal_size%7D%20bytes%22)
        # for downloading files with progress bar

        # fmt: off
        async with (
            self.aio_http_session.get(url, allow_redirects=True) as resp,
            aiofile.async_open(file_path, "wb") as f,
        ):
            chunk_size = 4096
            async for chunk in resp.content.iter_chunked(chunk_size):
                await f.write(chunk)
        # fmt: on

    async def get_versions(self: Self) -> dict:
        """
        Get all recent versions of factorio.

        Returns
        -------
        :class:`dict`
            A Json response containing the response data
        """
        async with self.aio_http_session.get(RELEASES_URL) as resp:
            return await resp.json()


    async def get_archived_versions(self: Self) -> list:
        """
        Get all/archived versions of factorio.

        Returns
        -------
        :class:`list`
            A list of all the versions
        """
        async with self.aio_http_session.get(ARCHIVE_URL) as resp:
            return await resp.json()

    async def get_downloaded(self: Self) -> AsyncGenerator["Path", None]:
        """
        Get all downloaded files.

        Returns
        -------
        :class:`list`
            A list of all the downloaded files
        """
        for i in DOWNLOADS_DIRECTORY.glob("*"):
            if i.is_file():
                yield i
