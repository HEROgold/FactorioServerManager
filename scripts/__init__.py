"""Module that contains some helpful functions for the project."""

from pathlib import Path
from typing import NoReturn, Self

import requests

from config import LOGIN_URL, SERVERS_DIRECTORY


def create_server_directory(server_name: str) -> None:
    """Create a directory for the server with the given name."""
    Path(SERVERS_DIRECTORY / server_name).mkdir(exist_ok=True, parents=True)


def download_server_files() -> NoReturn:
    """Download the files for the server with the given name."""
    raise NotImplementedError


class Login:  # noqa: D101
    http_session: requests.Session


    def __init__(self: Self) -> None:  # noqa: D107
        self.http_session = requests.Session()


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
        username_or_email : :class:`str`
            the username or the email for the login
        password : :class:`str`
            the password for logging in
        """
        csrf_token = self.get_csrf_details()
        data = {
            "username_or_email": username_or_email,
            "password": password,
            "csrf_token": csrf_token,
        }
        self.http_session.post(LOGIN_URL, data=data, timeout=5)
