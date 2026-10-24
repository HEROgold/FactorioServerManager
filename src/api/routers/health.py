"""Health check for the compose healthcheck and the deploy smoke test."""

import os
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session  # noqa: TC002 -- FastAPI resolves Depends at runtime

from api.deps import get_session

router = APIRouter()


class Health(BaseModel):
    """Whether the app and its database are up, and which build is running."""

    app: Literal["up"]
    # "up" once `migrate` has created alembic_version and the query succeeds.
    database: Literal["up", "down"]
    # The commit CI built the image from (FSM_COMMIT). "unknown" for local builds.
    commit: str


@router.get("/health")
def health(response: Response, db: Annotated[Session, Depends(get_session)]) -> Health:
    """Report the app and database status. Answers 503 when the database is down."""
    try:
        db.execute(text("SELECT version_num FROM alembic_version"))  # skylos: ignore[SKY-D211] -- literal SQL
        database: Literal["up", "down"] = "up"
    except SQLAlchemyError:
        database = "down"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    commit = os.getenv("FSM_COMMIT", "unknown")
    return Health(app="up", database=database, commit=commit)
