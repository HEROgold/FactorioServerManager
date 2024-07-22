"""Database models for the application."""

import hashlib
import logging
import random
from logging.handlers import RotatingFileHandler
from typing import Self

from flask_login import UserMixin
from sqlalchemy import (
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
)

from _types import FactorioInterface
from _types.data import Server
from config import DATABASE_PATH, SERVERS_DIRECTORY


logger: logging.Logger = logging.getLogger("sqlalchemy.engine")
handler = RotatingFileHandler(filename="sqlalchemy.log", backupCount=7, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())


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
        return self._factorio_token

    @factorio_token.setter
    def factorio_token(self: Self, token: str) -> None:
        self._factorio_token = token


    @property
    def display_name(self: Self) -> str:
        return self._display_name if self._display_name else self.email

    @classmethod
    def get_by_user_id(cls, user_id: int) -> Self | None:
        """
        Find existing user, and return it.

        Args:
        ----
            user_id (int): Identifier for the user.
        """
        with Session(engine) as session:
            logger.debug(f"Looking for user {user_id=}")

            if user := session.query(cls).where(cls.id == user_id).first():
                logger.debug(f"Returning user {user_id=}")
                return user
            return None

    @classmethod
    def fetch_by_email(cls, email: str) -> Self:
        """
        Find existing or create new user, and return it.

        Args:
        ----
            email (int): The email for the user.
        """
        with Session(engine) as session:
            logger.debug(f"Looking for user {email=}")

            if user := session.query(cls).where(cls.email == email).first():
                logger.debug(f"Returning user {email=}")
                return user

            logger.debug(f"Creating user {email=}")
            user = cls(email=email)
            session.add(user)
            session.commit()
            return user

    @staticmethod
    def encrypt_password(password: str) -> str:
        """
        Encrypt a password.

        Parameters
        ----------
        password: :class:`str`
            The password to encrypt

        Returns
        -------
        :class:`str`
        """
        random.seed(password)
        salt = str(random.random() * random.random())  # noqa: S311
        random.seed(None)
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def check_password(self: Self, password: str | None) -> bool:
        """
        Check if the user's stored password matches a given password.

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
        return self.password == self.encrypt_password(password)

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

Base().metadata.create_all(engine)


def main() -> None:
    """Run the main function."""


if __name__ == "__main__":
    main()
