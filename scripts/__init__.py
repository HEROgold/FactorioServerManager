"""Module that contains some helpful functions for the project."""

from pathlib import Path

import requests
from bs4 import BeautifulSoup

from config import ARCHIVE_URL, SERVERS_DIRECTORY


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
