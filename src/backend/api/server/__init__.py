"""Server related endpoints."""


from fastapi import APIRouter

from .download import router as download
from .manage import router as manage


router = APIRouter()
router.include_router(download)
router.include_router(manage)
