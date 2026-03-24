"""Database setup and session management for FastAPI."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.config import settings

# Use the existing database engine and models from FSM
from FSM._types.database import Base, User, engine

__all__ = ["engine", "Base", "User", "get_db"]


def get_db() -> Generator[Session, None, None]:
    """Get database session for dependency injection."""
    with Session(engine) as session:
        yield session
