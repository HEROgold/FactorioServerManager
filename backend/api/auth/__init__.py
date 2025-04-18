"""Module for authentication API."""

from fastapi import APIRouter

from .login import router as authentication_router


router = APIRouter()
router.include_router(authentication_router)
