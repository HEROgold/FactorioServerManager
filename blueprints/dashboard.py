"""Blueprint for dashboard page."""

from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup
from flask import Blueprint, render_template
from flask_login import login_required

from _types.enums import Build, Distro
from config import ARCHIVE_URL


this_filename = Path(__file__).name.split(".")[0]
bp = Blueprint(this_filename, __name__, url_prefix=f"/{this_filename}")


async def get_all_versions() -> list[str]:
    """Get all versions."""
    async with aiohttp.ClientSession() as session:
        resp = await session.get(ARCHIVE_URL)
        html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")

        return [
            i.text
            for i in soup.find_all("a", {"class": "slot-button-inline"})
        ]


@login_required
@bp.route("/dashboard")
async def dashboard() -> str:
    """Dashboard page."""
    builds = [i.name for i in Build]
    distros = [i.name for i in Distro]
    versions = await get_all_versions()
    return render_template(
        "dashboard.j2",
        builds=builds,
        distros=distros,
        versions=versions
    )
