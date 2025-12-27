"""Utilities for encrypting and decrypting Factorio tokens."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Final

from cryptography.fernet import Fernet

from FSM.config import PROJECT_DIRECTORY

TOKEN_KEY_ENV: Final[str] = "FSM_TOKEN_KEY"
TOKEN_KEY_FILE: Final[Path] = PROJECT_DIRECTORY / ".factorio_token.key"

logger = logging.getLogger(__name__)


def _build_cipher_from_value(value: str | bytes, source: str) -> Fernet:
    key_bytes = value.encode("utf-8") if isinstance(value, str) else value
    try:
        return Fernet(key_bytes)
    except ValueError as exc:  # pragma: no cover - critical misconfiguration path
        msg = (
            f"Invalid Factorio token key supplied via {source}. "
            "Provide a urlsafe base64-encoded 32-byte value."
        )
        raise RuntimeError(msg) from exc


def _load_cipher() -> Fernet:
    env_value = os.getenv(TOKEN_KEY_ENV)
    if env_value:
        return _build_cipher_from_value(env_value.strip(), f"${TOKEN_KEY_ENV}")

    if TOKEN_KEY_FILE.exists():
        token_value = TOKEN_KEY_FILE.read_text(encoding="utf-8").strip()
        return _build_cipher_from_value(token_value, str(TOKEN_KEY_FILE))

    key = Fernet.generate_key()
    TOKEN_KEY_FILE.write_text(key.decode("utf-8"), encoding="utf-8")
    try:
        if os.name != "nt":
            TOKEN_KEY_FILE.chmod(0o600)
    except OSError:  # pragma: no cover - permission errors vary per platform
        logger.debug("Unable to update permissions for %s", TOKEN_KEY_FILE, exc_info=True)
    logger.info("Factorio token encryption key created at %s", TOKEN_KEY_FILE)
    return Fernet(key)


_TOKEN_CIPHER: Fernet = _load_cipher()


def encrypt_factorio_token(value: str) -> bytes:
    """Encrypt a Factorio authentication token for storage."""
    return _TOKEN_CIPHER.encrypt(value.encode("utf-8"))


def decrypt_factorio_token(value: bytes) -> str:
    """Decrypt a stored Factorio authentication token."""
    return _TOKEN_CIPHER.decrypt(value).decode("utf-8")
