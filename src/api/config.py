""""Configuration for the fsm API."""
from pathlib import Path

from confkit import Config as BaseConfig


class Config[T](BaseConfig[T]):
    """Namespaced configuration for the fsm API."""

Config.set_file(Path("api_config.ini"))

class AppConfig:
    """Application configuration."""

    host = Config("host")
    port = Config(8000)
    sentry_dsn = Config("sentry_dsn")
    reload = Config(default=False)
    environment = Config("production")

app_config = AppConfig()

__all__ = ["Config", "app_config"]
