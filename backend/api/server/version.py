"""API endpoints for Factorio versions."""

from fastapi import APIRouter
from httpx import request

from models.factorio import AvailableVersions


router = APIRouter(prefix="/version")


@router.route("/all", methods=["GET"])
async def versions() -> AvailableVersions:
    """Get the available versions of Factorio."""
    return await request("get", "https://updater.factorio.com/get-available-versions").json()


@router.route("/latest", methods=["GET"])
async def latest_version() -> str:
    """Get the latest stable version of Factorio."""
    versions_data = await request("get", "https://updater.factorio.com/get-available-versions").json()
    return versions_data.get("stable", {}).get("alpha", "2.0.60")
