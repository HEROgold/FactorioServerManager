from FSM._types import database

def get_session():
    """Yield a SQLAlchemy Session using the existing engine in FSM._types.database."""
    # Using the existing Session class and engine from the project
    with database.Session(database.engine) as session:  # type: ignore[arg-type]
        yield session
