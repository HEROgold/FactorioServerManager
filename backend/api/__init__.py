"""Authentication API."""

from fastapi import APIRouter

from . import server
from .auth import login


router = APIRouter(prefix="/api")
router.include_router(login.router)
router.include_router(server.router)
