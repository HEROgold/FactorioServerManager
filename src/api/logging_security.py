"""Security helpers to keep secrets out of logs and error reports.

Tokens, passwords, session cookies and Factorio auth tokens must never reach
log files or Sentry. This module provides:

* :class:`RedactingFilter` - scrubs sensitive substrings from log records.
* :func:`scrub_event` - a Sentry ``before_send`` hook that strips cookies,
  auth headers and sensitive fields from outgoing events.
* :func:`configure_secure_logging` - quiets noisy HTTP client loggers (whose
  request URLs can contain ``?token=...``) and installs the redacting filter.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, override

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sentry_sdk.types import Event, Hint

# Substrings that mark a key/header/field as sensitive (case-insensitive).
SENSITIVE_KEYS: frozenset[str] = frozenset({
    "token",
    "password",
    "secret",
    "authorization",
    "cookie",
    "set-cookie",
    "fsm_session",
    "factorio_token",
})

_REDACTED = "[REDACTED]"

# Redact `key=value` / `key: value` pairs (query strings, form bodies, headers).
_PAIR_RE = re.compile(
    r"(?i)\b(token|password|secret|authorization|cookie|factorio_token)\b"
    r"(\s*[=:]\s*)"
    r"([^&\s,;'\"]+)",
)


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in SENSITIVE_KEYS)


def redact_text(text: str) -> str:
    """Replace the value portion of any sensitive ``key=value`` pair."""
    return _PAIR_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}{_REDACTED}", text)


class RedactingFilter(logging.Filter):
    """Logging filter that scrubs sensitive values from messages and args."""

    @override
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_text(record.msg)
        if record.args:
            record.args = _redact_args(record.args)
        return True


def _redact_args(args: Any) -> Any:  # noqa: ANN401 - mirrors logging's loose typing
    if isinstance(args, tuple):
        return tuple(redact_text(a) if isinstance(a, str) else a for a in args)
    if isinstance(args, dict):
        return {
            k: (_REDACTED if _is_sensitive_key(str(k)) else (redact_text(v) if isinstance(v, str) else v))
            for k, v in args.items()
        }
    return args


def _scrub_mapping(data: Mapping[Any, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for raw_key, value in data.items():
        key = str(raw_key)
        if _is_sensitive_key(key):
            cleaned[key] = _REDACTED
        elif isinstance(value, dict):
            cleaned[key] = _scrub_mapping(value)
        elif isinstance(value, str):
            cleaned[key] = redact_text(value)
        else:
            cleaned[key] = value
    return cleaned


def scrub_event(event: Event, _hint: Hint) -> Event | None:
    """Sentry ``before_send`` hook: remove cookies, auth headers and secrets."""
    request = event.get("request")
    if isinstance(request, dict):
        request.pop("cookies", None)
        headers = request.get("headers")
        if isinstance(headers, dict):
            request["headers"] = {
                str(k): (_REDACTED if _is_sensitive_key(str(k)) else v)
                for k, v in headers.items()
            }
        query_string = request.get("query_string")
        if isinstance(query_string, str):
            request["query_string"] = redact_text(query_string)
        data = request.get("data")
        if isinstance(data, dict):
            request["data"] = _scrub_mapping(data)
    for section in ("extra", "contexts"):
        value = event.get(section)
        if isinstance(value, dict):
            event[section] = _scrub_mapping(value)
    return event


def configure_secure_logging() -> None:
    """Quiet secret-leaking loggers and install the redacting filter."""
    redactor = RedactingFilter()
    # httpxyz/httpcore log request URLs at INFO; mod downloads carry ?token=...
    for noisy in ("httpxyz", "httpcorexyz", "httpx", "httpcore"):
        log = logging.getLogger(noisy)
        log.setLevel(logging.WARNING)
        log.addFilter(redactor)
    # Defense in depth: also scrub the root logger's output.
    logging.getLogger().addFilter(redactor)
