"""A custom JSON parser for confkit (stdlib ``json``, no msgspec dependency).

Implements confkit's :class:`~confkit.parsers.ConfkitParser` protocol so that
``Config`` descriptors can be backed by a JSON document. Nested objects are
addressed with dot-separated section paths (e.g. ``"visibility"`` ->
``{"public": ...}``), matching how confkit's own ``MsgspecParser`` behaves.

This is what lets the Factorio per-server settings files (which are deeply
nested JSON) be read and written through confkit.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from confkit.exceptions import ConfigPathConflictError
from confkit.sentinels import UNSET

if TYPE_CHECKING:
    from io import TextIOWrapper
    from pathlib import Path


class JsonParser:
    """Confkit parser that stores configuration in a JSON document."""

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}

    def read(self, file: Path) -> None:
        if not file.exists():
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("{}", encoding="utf-8")
            self.data = {}
            return
        try:
            loaded = json.loads(file.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            loaded = {}
        self.data = loaded if isinstance(loaded, dict) else {}

    def write(self, io: TextIOWrapper) -> None:
        io.write(json.dumps(self.data, indent=2))

    def _navigate(self, section: str, *, create: bool) -> dict[str, Any] | None:
        if not section:
            return self.data
        current: dict[str, Any] = self.data
        parts = section.split(".")
        for index, part in enumerate(parts):
            existing = current.get(part)
            if existing is None:
                if not create:
                    return None
                current[part] = {}
                existing = current[part]
            if not isinstance(existing, dict):
                if create:
                    path = ".".join(parts[: index + 1])
                    msg = f"Cannot navigate to section '{section}': '{path}' is a scalar, not a section."
                    raise ConfigPathConflictError(msg)
                return None
            current = existing
        return current

    def has_section(self, section: str) -> bool:
        return self._navigate(section, create=False) is not None

    def set_section(self, section: str) -> None:
        self._navigate(section, create=True)

    def add_section(self, section: str) -> None:
        self.set_section(section)

    def set_option(self, option: str) -> None:
        """Options are written via :meth:`set`; nothing to do here."""

    def has_option(self, section: str, option: str) -> bool:
        data = self._navigate(section, create=False)
        return data is not None and option in data

    def remove_option(self, section: str, option: str) -> None:
        data = self._navigate(section, create=False)
        if data is not None and option in data:
            del data[option]

    def get(self, section: str, option: str, fallback: str = UNSET) -> str:
        data = self._navigate(section, create=False)
        if data is None or option not in data:
            return str(fallback) if fallback is not UNSET else UNSET
        return str(data[option])

    def set(self, section: str, option: str, value: object) -> None:
        data = self._navigate(section, create=True)
        if data is None:  # pragma: no cover - create=True always returns a dict
            msg = f"Cannot set option '{option}' in section '{section}'."
            raise ConfigPathConflictError(msg)
        data[option] = value
