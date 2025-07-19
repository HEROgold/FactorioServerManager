"""Main FastAPI application."""

from typing import Annotated

import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from api import router as api_router
from models.user import User, get_current_user


# Create the FastAPI application
app = fastapi.FastAPI(
    title="Factorio Server Manager",
    description="API for managing Factorio game servers",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include API router
app.include_router(api_router)

@app.get("/")
async def root() -> RedirectResponse:
    """Redirect to the API documentation."""
    return RedirectResponse(url="/docs")

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# User endpoints that aren't part of the main API router
@app.get("/api/users/me")
async def read_users_me(current_user: Annotated[User, fastapi.Depends(get_current_user)]) -> User:
    """Get the current user."""
    return current_user
