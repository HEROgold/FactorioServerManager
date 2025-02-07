"""Main FastAPI application."""
import fastapi
from api import router as api_router


app = fastapi.FastAPI()
app.include_router(api_router)
