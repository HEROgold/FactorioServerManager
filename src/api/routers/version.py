"""API router for fetching available Factorio versions from the official archive page."""
from typing import TYPE_CHECKING

import aiohttp
from bs4 import BeautifulSoup
from fastapi import APIRouter

from api._types import Version
from fsm.config import ARCHIVE_URL

if TYPE_CHECKING:
    from collections.abc import Generator

router = APIRouter()


async def fetch_html() -> str:
    """Fetch the HTML content of the Factorio version archive page."""
    timeout = aiohttp.ClientTimeout(total=5)

    async with aiohttp.ClientSession(timeout=timeout) as session, session.get(ARCHIVE_URL) as response:
        response.raise_for_status()
        return await response.text()

async def fetch_versions() -> Generator[Version]:
    """Fetch available Factorio versions from the official archive page."""
    html = await fetch_html()
    soup = BeautifulSoup(html, "html.parser")
    return (
        Version(i.text.strip())
        for i in soup.find_all("a", {"class": "slot-button-inline"})
        if i.text and i.text.strip()
    )

@router.get("/versions")
async def get_all_download_versions() -> list[Version]:
    """Get all versions."""
    return [Version("latest"), Version("stable"), *await fetch_versions()]
