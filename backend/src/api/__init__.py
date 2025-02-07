"""Authentication API."""

from fastapi import APIRouter

from .auth import login


router = APIRouter()
router.include_router(login.router)
