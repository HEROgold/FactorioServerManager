""""Configuration for the FSM API."""
from pathlib import Path

from confkit import Config as BaseConfig


class Config(BaseConfig):
    """Namespaced configuration for the FSM API."""

Config.set_file(Path("api_config.ini"))

class AppConfig:
    """Application configuration."""

    host = Config("host")
    port = Config(8000)
    sentry_dsn = Config("dns")
    reload = Config(default=False)

app_config = AppConfig()
