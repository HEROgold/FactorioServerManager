"""Module that contains some helpful functions for the project."""

from pathlib import Path
from typing import NoReturn

from selenium import webdriver

from conifg import LOGIN_URL, SERVERS_DIRECTORY


def create_server_directory(server_name: str) -> None:
    """Create a directory for the server with the given name."""
    Path(SERVERS_DIRECTORY / server_name).mkdir(exist_ok=True, parents=True)


def download_server_files(server_name: str) -> NoReturn:
    """Download the files for the server with the given name."""
    raise NotImplementedError


def get_login_details() -> NoReturn:
    # use selenium to open default browser and get login details
    raise NotImplementedError

