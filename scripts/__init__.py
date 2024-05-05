"""Module that contains some helpful functions for the project."""

from collections.abc import Generator
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from config import ARCHIVE_URL, DOWNLOADS_DIRECTORY, SERVERS_DIRECTORY


def create_server_directory(server_name: str) -> None:
    """Create a directory for the server with the given name."""
    Path(SERVERS_DIRECTORY / server_name).mkdir(exist_ok=True, parents=True)


def get_all_download_versions() -> list[str]:
    """Get all versions."""
    resp = requests.get(ARCHIVE_URL, timeout=5)
    soup = BeautifulSoup(resp.text, "html.parser")

    return [
        i.text.strip()
        for i in soup.find_all("a", {"class": "slot-button-inline"})
    ]

def get_downloaded() -> Generator["Path", Any, None]:
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

def get_installed() -> Generator["Path", Any, None]:
    """
    Get all installed files.

    Returns
    -------
    :class:`list`
        A list of all the installed files
    """
    for i in SERVERS_DIRECTORY.glob("*"):
        if i.is_dir():
            yield i
