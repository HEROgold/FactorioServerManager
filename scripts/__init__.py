"""Module that contains some helpful functions for the project."""

import tarfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

import aiofile
import aiohttp
import requests
from bs4 import BeautifulSoup

from config import ARCHIVE_URL, DOWNLOADS_DIRECTORY, SERVERS_DIRECTORY


async def create_server_directory(server_name: str) -> None:
    """Create a directory for the server with the given name."""
    Path(SERVERS_DIRECTORY / server_name).mkdir(exist_ok=True, parents=True)


async def get_all_download_versions() -> list[str]:
    """Get all versions."""
    async with aiohttp.ClientSession().get(ARCHIVE_URL) as resp:
        soup = BeautifulSoup(await resp.text(), "html.parser")

        return [
            i.text.strip()
            for i in soup.find_all("a", {"class": "slot-button-inline"})
        ]


async def get_downloaded() -> AsyncGenerator["Path", None]:
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

async def get_installed() -> AsyncGenerator["Path", None]:
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


async def install_server(name: str, port: int) -> None:
    """
    Install a server with the given name and port. Creates a cfg file with server settings.

    Parameters
    ----------
    name: :class:`str`
        The name of the server
    port: :class:`int`
        The port of the server
    """
    zip_file = DOWNLOADS_DIRECTORY/name
    server_directory = SERVERS_DIRECTORY/name

    server_directory.mkdir(exist_ok=True, parents=True)

    with tarfile.open(zip_file, "r") as f:
        f.extractall(server_directory, filter="data")

    async with aiofile.async_open(server_directory/"settings.cfg", "w") as f:
        settings = {
            "name": name,
            "port": port,
        }

        for i in settings:
            await f.write(f"{i}={settings[i]}")
            await f.write("\n")
