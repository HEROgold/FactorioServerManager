"""Alembic environment: run the migrations against ``sqlalchemy.url``."""

from alembic import context
from sqlalchemy import create_engine

from api._types.database import Base
from api.constants import DATABASE_PATH

# The models, so `revision --autogenerate` can diff them against the database.
target_metadata = Base.metadata


def run_migrations() -> None:
    """Run the pending migrations in one transaction."""
    # api.migrate sets the URL; the alembic CLI uses the app's database.
    url = context.config.get_main_option("sqlalchemy.url")
    url = url or f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            # SQLite can't ALTER most constraints in place, so autogenerate
            # writes batch operations, which copy the table instead.
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                render_as_batch=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run_migrations()
