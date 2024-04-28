from typing import Self

import aiohttp
import requests

from _types.enums import Build, Distro
from config import ARCHIVE_URL, DOWNLOADS_DIRECTORY, LOGIN_URL, RELEASES_URL


class FactorioInterface:
    http_session: requests.Session

    def __init__(self: Self) -> None:
        self.http_session = requests.Session()
        self.aio_http_session = aiohttp.ClientSession()

    def get_csrf_details(self: Self) -> str:
        """
        Get the csrf token from the login page.

        Returns
        -------
        :class:`str`
            the csrf token
        """
        req = self.http_session.get(LOGIN_URL, timeout=5)
        j = req.json()
        return str(j["csrf_token"])

    def login_user(self: Self, username_or_email: str, password: str) -> None:
        """
        Log in the user with the given username and password.

        Parameters
        ----------
        username_or_email: :class:`str`
            the username or the email for the login
        password: :class:`str`
            the password for logging in
        """
        csrf_token = self.get_csrf_details()
        data = {
            "username_or_email": username_or_email,
            "password": password,
            "csrf_token": csrf_token,
        }
        self.http_session.post(LOGIN_URL, data=data, timeout=5)

    @staticmethod
    def is_downloadable(url: str) -> bool:
        """Is the url a downloadable resource."""
        h = requests.head(url, allow_redirects=True, timeout=5)
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

    def download_server_files(self: Self, build: Build, distro: Distro, version: str = "latest") -> None:
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
        if not self.is_downloadable(url):
            msg = "The url does not point to a downloadable resource"
            raise ValueError(msg)

        with DOWNLOADS_DIRECTORY.open("wb") as f:
            for chunk in self.http_session.get(url, allow_redirects=True).iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                else:
                    break

    def get_versions(self: Self) -> dict:
        """
        Get all recent versions of factorio.

        Returns
        -------
        :class:`dict`
            A Json response containing the response data
        """
        return self.http_session.get(RELEASES_URL).json()

    def get_archived_versions(self: Self) -> list:
        """
        Get all/archived versions of factorio.

        Returns
        -------
        :class:`list`
            A list of all the versions
        """
        return self.http_session.get(ARCHIVE_URL).json()
