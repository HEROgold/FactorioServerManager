"""API endpoints for Factorio versions."""

from fastapi import APIRouter
from httpx import request

from backend.models.factorio import AvailableVersions


router = APIRouter(prefix="/version")


@router.route("/all", methods=["GET"])
async def versions() -> AvailableVersions:
    """Get the available versions of Factorio."""
    return await request("get", "https://updater.factorio.com/get-available-versions").json()
