"""api.migrate: fresh databases, databases from before Alembic, and reruns."""

import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from alembic import command
from hypothesis import given, settings
from hypothesis import strategies as st

from api.migrate import alembic_config, upgrade
from tests.strategies import display_names, emails, passwords

HEAD = "0002"
USERS_COLUMNS = ["id", "password", "email", "_display_name", "factorio_token"]

users = st.lists(st.tuples(emails, passwords, display_names), max_size=5)


def _path(database_url: str) -> str:
    return database_url.removeprefix("sqlite:///")


def _connect(database_url: str) -> closing[sqlite3.Connection]:
    # sqlite3's own context manager commits but doesn't close, and Windows
    # can't delete a file that is still open.
    return closing(sqlite3.connect(_path(database_url), autocommit=True))


def _revision(database_url: str) -> str:
    with _connect(database_url) as db:
        return db.execute("SELECT version_num FROM alembic_version").fetchone()[0]


def _users_columns(database_url: str) -> list[str]:
    with _connect(database_url) as db:
        return [row[1] for row in db.execute("PRAGMA table_info(users)")]


def test_fresh_database_reaches_head(database_url: str) -> None:
    upgrade(database_url)

    assert _revision(database_url) == HEAD
    assert _users_columns(database_url) == USERS_COLUMNS


def test_rerun_changes_nothing(database_url: str) -> None:
    upgrade(database_url)
    upgrade(database_url)

    assert _revision(database_url) == HEAD


def test_models_match_the_migrations(database_url: str) -> None:
    upgrade(database_url)

    # Raises if `revision --autogenerate` would find a difference.
    command.check(alembic_config(database_url))


@settings(max_examples=25, deadline=None)
@given(rows=users, with_token=st.booleans())
def test_pre_alembic_database_keeps_its_users(
    rows: list[tuple[str, str, str]],
    *,
    with_token: bool,
) -> None:
    """A database made by the old import-time create_all, with or without the ALTER."""
    with tempfile.TemporaryDirectory() as directory:
        database_url = f"sqlite:///{Path(directory) / 'legacy.db'}"
        token_column = ", factorio_token BLOB" if with_token else ""
        with _connect(database_url) as db:
            db.execute(
                "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "password VARCHAR, email VARCHAR, "
                f"_display_name VARCHAR{token_column})",
            )
            db.executemany(
                "INSERT INTO users (email, password, _display_name) VALUES (?, ?, ?)",
                rows,
            )

        upgrade(database_url)

        assert _revision(database_url) == HEAD
        assert _users_columns(database_url) == USERS_COLUMNS
        with _connect(database_url) as db:
            kept = db.execute(
                "SELECT email, password, _display_name FROM users ORDER BY id",
            ).fetchall()
        assert kept == rows
