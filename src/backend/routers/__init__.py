"""Routers package for API."""

# ruff: noqa: N999  - keep package naming consistent with top-level FSM package
from . import dashboard, login, mods, server

__all__ = ["dashboard", "login", "mods", "server"]
