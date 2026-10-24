"""Test harness: the app's secrets, and a fresh SQLite database per test.

The app resolves its session secret and token key when ``api`` is first
imported, so they are set here, before any test module imports it.
"""

import os
import secrets

import pytest  # skylos: ignore[SKY-D223] -- dev dependency
from cryptography.fernet import Fernet

os.environ.setdefault("FSM_SECRET_KEY", secrets.token_hex(64))
os.environ.setdefault("FSM_TOKEN_KEY", Fernet.generate_key().decode())

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from api.deps import get_session
from api.main import app

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


@pytest.fixture
def database_url(tmp_path: Path) -> str:
    """URL of an empty SQLite database that only this test uses."""
    return f"sqlite:///{tmp_path / 'fsm.db'}"


@pytest.fixture
def client(database_url: str) -> Iterator[TestClient]:
    """Serve the app, with every request's session on this test's database."""
    engine = create_engine(database_url)

    def session() -> Iterator[Session]:
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_session] = session
    yield TestClient(app)
    app.dependency_overrides.pop(get_session)
    engine.dispose()
