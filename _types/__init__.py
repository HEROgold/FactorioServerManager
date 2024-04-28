from typing import Self

import aiofile
import aiohttp

from _types.enums import Build, Distro
from config import ARCHIVE_URL, DOWNLOADS_DIRECTORY, LOGIN_URL, RELEASES_URL


class FactorioInterface:
    aio_http_session: aiohttp.ClientSession

    def __init__(self: Self) -> None:
        self.aio_http_session = aiohttp.ClientSession()

    async def get_csrf_details(self: Self) -> str:
        """
        Get the csrf token from the login page.

        Returns
        -------
        :class:`str`
            the csrf token
        """
        req = await self.aio_http_session.get(LOGIN_URL, timeout=5)
        j = await req.json()
        return str(j["csrf_token"])

    async def login_user(self: Self, username_or_email: str, password: str) -> None:
        """
        Log in the user with the given username and password.

        Parameters
        ----------
        username_or_email: :class:`str`
            the username or the email for the login
        password: :class:`str`
            the password for logging in
        """
        csrf_token = await self.get_csrf_details()
        data = {
            "username_or_email": username_or_email,
            "password": password,
            "csrf_token": csrf_token,
        }
        await self.aio_http_session.post(LOGIN_URL, data=data, timeout=5)

    async def is_downloadable(self: Self, url: str) -> bool:
        """Is the url a downloadable resource."""
        h = await self.aio_http_session.head(url, allow_redirects=True)
        header = h.headers
        content_type = header.get("content-type")

        # fmt: off
        if (
            content_type is None
            or "text" in content_type.lower()
            or "html" in content_type.lower()
        ):
            return False
        return True
        # fmt: on

    async def download_server_files(self: Self, build: Build, distro: Distro, version: str = "latest") -> None:
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

        Raises
        ------
        :class:`ValueError`
            If any values are invalid
        """
        url = f"https://www.factorio.com/get-download/{version}/{build.name}/{distro.name}"
        if not await self.is_downloadable(url):
            msg = f"The url does not point to a downloadable resource: {url=}"
            raise ValueError(msg)

        # fmt: off
        async with (
            aiofile.async_open(DOWNLOADS_DIRECTORY, "wb") as f,
            self.aio_http_session.get(url, allow_redirects=True) as resp
        ):
            await f.write(await resp.read())
        # fmt: on

    async def get_versions(self: Self) -> dict:
        """
        Get all recent versions of factorio.

        Returns
        -------
        :class:`dict`
            A Json response containing the response data
        """
        resp = await self.aio_http_session.get(RELEASES_URL)
        return await resp.json()

    async def get_archived_versions(self: Self) -> list:
        """
        Get all/archived versions of factorio.

        Returns
        -------
        :class:`list`
            A list of all the versions
        """
        resp = await self.aio_http_session.get(ARCHIVE_URL)
        return await resp.json()
