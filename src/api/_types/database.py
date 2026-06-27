"""Database models for the application."""
import logging
from logging import getLogger
from typing import Self

import bcrypt
import httpxyz
from cryptography.fernet import InvalidToken
from sqlalchemy import (
    Integer,
    LargeBinary,
    String,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
)

from api._types import FactorioBridge
from api._types.data import Server
from api._types.factorio_interface import ModsInterface
from api.constants import DATABASE_PATH, SERVERS_DIRECTORY, HTTPConfig
from api.security import decrypt_factorio_token, encrypt_factorio_token

logger: logging.Logger = getLogger("database")
logger.setLevel(logging.DEBUG)


engine = create_engine(f"sqlite:///{DATABASE_PATH}")

client = httpxyz.AsyncClient(
    http2=True,
    timeout=HTTPConfig.timeout,
    follow_redirects=True,
)
mods = ModsInterface(client)

class Base(DeclarativeBase):
    """Subclass of DeclarativeBase with customizations."""

    # Column names whose values must never appear in logs / reprs / errors.
    _SENSITIVE_COLUMNS: frozenset[str] = frozenset({
        "password",
        "factorio_token_encrypted",
    })

    def __repr__(self: Self) -> str:
        """Return a representation with sensitive columns redacted."""
        parts = [
            f"{key}={'[REDACTED]' if key in self._SENSITIVE_COLUMNS else value!r}"
            for key, value in self.__dict__.items()
            if not key.startswith("_sa_")
        ]
        return f"{type(self).__name__}({', '.join(parts)})"


class User(Base):
    """User model for the application. Inherits from UserMixin and Base."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    password: Mapped[str] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=True)
    _display_name: Mapped[str] = mapped_column(String, nullable=True, unique=False)
    factorio_token_encrypted: Mapped[bytes | None] = mapped_column(
        "factorio_token",
        LargeBinary,
        nullable=True,
    )

    @property
    def fi(self: Self) -> FactorioBridge:
        if getattr(self, "_fi", None) is None:
            self._fi = FactorioBridge(client, mods)
        return self._fi

    @fi.setter
    def fi(self: Self, fi: FactorioBridge) -> None:
        self._fi = fi

    @property
    def factorio_token(self: Self) -> str | None:
        encrypted = self.factorio_token_encrypted
        if not encrypted:
            return None
        try:
            return decrypt_factorio_token(encrypted)
        except InvalidToken:  # pragma: no cover - indicates on-disk corruption
            logger.warning(
                "Unable to decrypt Factorio token for user %s; clearing stored value.",
                self.email,
            )
            self.factorio_token_encrypted = None
            return None

    @factorio_token.setter
    def factorio_token(self: Self, token: str | None) -> None:
        if not token:
            self.factorio_token_encrypted = None
            return
        self.factorio_token_encrypted = encrypt_factorio_token(token)

    @property
    def fi(self: Self) -> FactorioBridge:
        """Return a FactorioInterface instance authenticated with the user's token."""
        if not hasattr(self, "_fi") or self._fi is None:
            self._fi = FactorioBridge(client, mods)
        return self._fi

    @property
    def display_name(self: Self) -> str:
        return self._display_name or self.email

    @classmethod
    def fetch_by_email(cls, email: str) -> Self:
        """Find existing or create new user, and return it.

        Args:
        ----
            email (str): The email for the user.

        """
        with Session(engine) as session:
            logger.debug(f"Looking for user {email=}")

            if user := session.query(cls).where(cls.email == email).first():
                logger.debug(f"Returning user {email=}")
                session.expunge(user)
                return user

            logger.debug(f"Creating user {email=}")
            user = cls(email=email)
            session.add(user)
            session.commit()
            session.refresh(user)
            session.expunge(user)
            return user

    @property
    def servers(self: Self) -> dict[str, Server]:
        servers = SERVERS_DIRECTORY/str(self.id)
        if not servers.exists():
            servers.mkdir(parents=True)

        if getattr(self, "_servers", None) is None:
            self._servers: dict[str, Server] = {}
            for server in servers.iterdir():
                self._servers[server.name] = Server(server.name, self)
        return self._servers

    def persist_factorio_token(self: Self, token: str) -> None:
        """Persist the encrypted Factorio token for this user."""
        self.factorio_token = token
        with Session(engine) as session:
            db_user = session.get(User, self.id)
            if db_user is None:
                msg = f"Unable to locate user {self.id} while saving token"
                raise ValueError(msg)
            db_user.factorio_token = token
            session.commit()
            session.refresh(db_user)
            self.factorio_token_encrypted = db_user.factorio_token_encrypted


    def add_server(self: Self, server: Server) -> None:
        if server.name in self.servers:
            msg = f"Server {server.name} already exists"
            raise ValueError(msg)
        self._servers[server.name] = server

    async def remove_server(self: Self, server: Server) -> None:
        if server.name not in self.servers:
            msg = f"Server {server.name} does not exist"
            raise ValueError(msg)
        await self._servers[server.name].remove()

def _ensure_user_schema() -> None:
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns(User.__tablename__)}
    if "factorio_token" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN factorio_token BLOB"))


Base().metadata.create_all(engine)
_ensure_user_schema()


def main() -> None:
    """Run the main function."""


if __name__ == "__main__":
    main()
