"""Database models for the application."""

import logging
from typing import Self

import bcrypt
from cryptography.fernet import InvalidToken
from flask_login import UserMixin
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

from FSM._types import FactorioInterface
from FSM._types.data import Server
from FSM.config import DATABASE_PATH, SERVERS_DIRECTORY
from FSM.logging_utils import get_logger
from FSM.security import decrypt_factorio_token, encrypt_factorio_token

logger: logging.Logger = get_logger("sqlalchemy.engine")
logger.setLevel(logging.DEBUG)


engine = create_engine(f"sqlite:///{DATABASE_PATH}")


class Base(DeclarativeBase):
    """Subclass of DeclarativeBase with customizations."""

    def __repr__(self: Self) -> str:
        """Return a string representation of the object."""
        return str(self.__dict__)


class User(Base, UserMixin):
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
    def fi(self: Self) -> FactorioInterface:
        if getattr(self, "_fi", None) is None:
            self._fi = FactorioInterface()
        return self._fi

    @fi.setter
    def fi(self: Self, fi: FactorioInterface) -> None:
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
    def fi(self: Self) -> FactorioInterface:
        """Return a FactorioInterface instance authenticated with the user's token."""
        if not self._fi:
            self._fi = FactorioInterface()
        return self._fi

    @property
    def display_name(self: Self) -> str:
        return self._display_name or self.email

    @classmethod
    def get_by_user_id(cls, user_id: int) -> Self | None:
        """Find existing user, and return it.

        Args:
        ----
            user_id (int): Identifier for the user.

        """
        with Session(engine) as session:
            logger.debug(f"Looking for user {user_id=}")

            if user := session.query(cls).where(cls.id == user_id).first():
                logger.debug(f"Returning user {user_id=}")
                session.expunge(user)
                return user
            return None

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

    @staticmethod
    def encrypt_password(password: str) -> str:
        """Encrypt a password.

        Parameters
        ----------
        password: :class:`str`
            The password to encrypt

        Returns
        -------
        :class:`str`

        """
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self: Self, password: str | None) -> bool:
        """Check if the user's stored password matches a given password.

        Parameters
        ----------
        password: :class:`str`
            The password to match against

        Returns
        -------
        :class:`bool`

        """
        if password is None:
            return False
        return bcrypt.checkpw(password.encode(), self.password.encode())

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

    def remove_server(self: Self, server: Server) -> None:
        if server.name not in self.servers:
            msg = f"Server {server.name} does not exist"
            raise ValueError(msg)
        self._servers[server.name].remove()

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
