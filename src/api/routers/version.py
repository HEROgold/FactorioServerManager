"""API router for fetching available Factorio versions from the official archive page."""
from typing import TYPE_CHECKING

import httpxyz
from bs4 import BeautifulSoup
from fastapi import APIRouter

from api._types import Version
from api.constants import ARCHIVE_URL, DEFAULT_VERSION

if TYPE_CHECKING:
    from collections.abc import Generator

router = APIRouter()


async def fetch_html() -> str:
    """Fetch the HTML content of the Factorio version archive page."""
    async with httpxyz.AsyncClient(http2=True, timeout=5.0, follow_redirects=True) as client:
        response = await client.get(ARCHIVE_URL)
        response.raise_for_status()
        return response.text

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
async def get_all_download_versions() -> list[str]:
    """Get all versions."""
    return [Version("latest"), Version(DEFAULT_VERSION), *await fetch_versions()]
