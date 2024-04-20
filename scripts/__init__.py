"""Module that contains some helpful functions for the project."""

from pathlib import Path

from config import SERVERS_DIRECTORY


def create_server_directory(server_name: str) -> None:
    """Create a directory for the server with the given name."""
    Path(SERVERS_DIRECTORY / server_name).mkdir(exist_ok=True, parents=True)

