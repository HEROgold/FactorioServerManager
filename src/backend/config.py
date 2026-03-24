"""Configuration settings for FastAPI backend."""

import os
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Environment
    ENVIRONMENT: Literal["development", "production"] = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = os.getenv("FSM_SECRET_KEY", "")
    TOKEN_KEY: str = os.getenv("FSM_TOKEN_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    SERVER_OPERATION_COOLDOWN_SECONDS: int = 30  # Cooldown for create/update operations

    # Database
    DATABASE_URL: str = f"sqlite:///{Path.cwd()}/database.db"

    # Directories
    SERVERS_DIRECTORY: Path = Path.cwd() / "servers"

    # Docker
    DOCKER_CONTAINER_PREFIX: str = "factorio-headless"
    DOCKER_IMAGE: str = "factoriotools/factorio"

    # Public IP for server display
    PUBLIC_IP: str | None = None

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure necessary keys exist
if not settings.SECRET_KEY:
    from cryptography.fernet import Fernet
    key_file = Path(".flask_secret.key")
    if key_file.exists():
        settings.SECRET_KEY = key_file.read_text().strip()
    else:
        settings.SECRET_KEY = Fernet.generate_key().decode()
        key_file.write_text(settings.SECRET_KEY)

if not settings.TOKEN_KEY:
    from cryptography.fernet import Fernet
    key_file = Path(".factorio_token.key")
    if key_file.exists():
        settings.TOKEN_KEY = key_file.read_text().strip()
    else:
        settings.TOKEN_KEY = Fernet.generate_key().decode()
        key_file.write_text(settings.TOKEN_KEY)
