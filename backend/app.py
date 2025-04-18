"""Main FastAPI application."""

from typing import Annotated

import fastapi
from api import router as api_router
from fastapi.middleware.cors import CORSMiddleware
from models.user import User, get_current_user


app = fastapi.FastAPI()
app.include_router(api_router)


origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, fastapi.Depends(get_current_user)]) -> User:
    """Get the current user."""
    return current_user
