"""Database session provider for API routers.

Prefer `herogold` when available, otherwise fall back to the project's
existing SQLAlchemy `Session` in `FSM._types.database`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

from FSM._types import database

try:
    import herogold  # type: ignore[import]

    if hasattr(herogold, "get_session"):
        def get_session() -> Generator:
            """Yield a session provided by herogold.get_session()."""
            with herogold.get_session() as session:
                yield session
    elif hasattr(herogold, "db") and hasattr(herogold.db, "get_session"):
        def get_session() -> Generator:
            """Yield a session provided by herogold.db.get_session()."""
            with herogold.db.get_session() as session:
                yield session
    else:  # pragma: no cover - fallback if herogold API differs
        def get_session() -> Generator:
            """Yield a SQLAlchemy session as a fallback."""
            with database.Session(database.engine) as session:
                yield session
except (ImportError, AttributeError):
    # herogold not available or import failed; use existing SQLAlchemy session
    def get_session() -> Generator:
        """Yield a SQLAlchemy session when herogold is not present."""
        with database.Session(database.engine) as session:
            yield session
