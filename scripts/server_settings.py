"""Module that contains some helpful functions for managing servers."""



from collections.abc import AsyncGenerator

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
