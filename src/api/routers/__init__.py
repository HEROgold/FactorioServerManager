"""Routers package for API."""


from . import (
    dashboard,
    login,
    mods,
    server_lifecycle,
    server_logs,
    server_public,
    server_rcon,
    server_settings,
    server_shared,
    user,
    version,
)

__all__ = [
    "dashboard",
    "login",
    "mods",
    "server_lifecycle",
    "server_logs",
    "server_public",
    "server_rcon",
    "server_settings",
    "server_shared",
    "user",
    "version",
]
