"""Guarded raw JSON file I/O for the msgspec-backed settings documents.

msgspec.json handles the actual decode/encode; this module only enforces the
safety invariants the settings files need: refuse to follow symlinks, and cap
how large a per-server config file can be before it's read into memory.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# Per-server settings documents are small, hand-edited JSON; anything larger
# is not a legitimate config file and is refused rather than loaded whole.
MAX_BYTES = 5 * 1024 * 1024


def read_bytes(file: Path) -> bytes:
    """Return ``file``'s raw bytes, creating an empty ``{}`` document if missing."""
    if file.is_symlink():
        msg = f"Refusing to follow symlink config file: {file}"
        raise ValueError(msg)
    if not file.is_file():
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"{}")
        return b"{}"
    if file.stat().st_size > MAX_BYTES:
        msg = f"Config file too large (> {MAX_BYTES} bytes): {file}"
        raise ValueError(msg)
    return file.read_bytes()


def write_bytes(file: Path, data: bytes) -> None:
    """Write ``data`` to ``file``, refusing to write over a symlink."""
    if file.is_symlink():
        msg = f"Refusing to write over symlink config file: {file}"
        raise ValueError(msg)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(data)  # skylos: ignore -- symlink-checked above
