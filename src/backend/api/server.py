"""Server API endpoints."""
from fastapi import APIRouter


router = APIRouter(prefix="/server", tags=["server"])

@router.get("/list")
async def list_servers(user):
    return {"servers": []}
