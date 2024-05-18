"""Module that contains some helpful functions for managing servers."""



from collections.abc import AsyncGenerator
from pathlib import Path

import aiofile

from config import SERVERS_DIRECTORY


async def get_server_settings(name: str) -> AsyncGenerator[tuple[str, str], None]:
    """Get custom server settings."""
    server_directory = SERVERS_DIRECTORY/name

    async with aiofile.async_open(server_directory/"settings.cfg", "r") as f:
        async for line in f:
            name, value = line.split("=") # type: ignore[reportAssignmentType]
            yield name, str(value)

async def update_server_settings(name: str, settings: dict[str, str]) -> None:
    """Update custom server settings."""
    server_directory = SERVERS_DIRECTORY/name

    async with aiofile.async_open(server_directory/"settings.cfg", "w") as f:
        async for line in f:
            for name, value in settings.items():
                if line.startswith(name): # type: ignore[reportArgumentType]
                    await f.write(f"{name}={value}\n")

async def get_server_directories(name: str) -> tuple[Path, Path, Path, Path]:
    """Get the required directories and executable for a given server."""
    server_directory = SERVERS_DIRECTORY/name

    if "linux" in name:
        executable = server_directory/"factorio/bin/factorio"

    data = server_directory/"data"
    map_generation_settings = data/"map-gen-settings.json"
    map_settings = data/"map-settings.json"
    server_settings = data/"server-settings.json"

    return executable, map_generation_settings, map_settings, server_settings
