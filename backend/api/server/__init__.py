"""Server related endpoints."""


from fastapi import APIRouter

from .manage import router as manage
from .version import router as version


router = APIRouter(prefix="/server")
router.include_router(manage)
router.include_router(version)
