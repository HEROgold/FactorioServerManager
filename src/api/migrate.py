"""Bring the database schema up to date.

Deploys run ``python -m api.migrate`` in the ``migrate`` service before the
backend starts. Run it by hand before a local ``uvicorn`` too.

A failed deploy rolls back the images but not the schema, so each revision
must keep the previous release working: add a column in one release, and drop
the old one in a later release.

Each migration is a revision under ``api/migrations/versions``. To add one,
change the models, then generate it and check the result::

    uv run alembic revision --autogenerate -m "<what>"
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from api.constants import DATABASE_PATH

MIGRATIONS = Path(__file__).parent / "migrations"

# A database from before Alembic has tables but no alembic_version. Its users
# table is at BASELINE, or at LEGACY_HEAD once the old import-time ALTER added
# the factorio_token column.
BASELINE = "0001"
LEGACY_HEAD = "0002"


def alembic_config(database_url: str) -> Config:
    """Return the Alembic config for the database at ``database_url``."""
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _legacy_revision(database_url: str) -> str | None:
    """Return the revision a pre-Alembic database is at, or None if it isn't one."""
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        if "alembic_version" in tables or "users" not in tables:
            return None
        columns = {column["name"] for column in inspector.get_columns("users")}
    finally:
        engine.dispose()
    return LEGACY_HEAD if "factorio_token" in columns else BASELINE


def upgrade(database_url: str) -> None:
    """Migrate the database at ``database_url`` to the newest revision."""
    config = alembic_config(database_url)
    if revision := _legacy_revision(database_url):
        command.stamp(config, revision)
    command.upgrade(config, "head")


if __name__ == "__main__":
    upgrade(f"sqlite:///{DATABASE_PATH}")
