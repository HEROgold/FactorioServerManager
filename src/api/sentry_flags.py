"""Sentry generic feature-flag *change tracking*.

Sentry can correlate feature-flag changes with issue spikes if we POST a signed
event to its generic webhook whenever a flag flips. Flags are declared in
`api.config.FeatureFlags` and toggled by editing `api_config.ini`; there is no
admin UI. We therefore watch the ini (confkit's `FileWatcher`, same mechanism the
SSE endpoint uses), diff the flag snapshot on each change, and emit the deltas.

Payload/signature follow Sentry's generic provider spec: a JSON body signed with
HMAC-SHA256 over the raw bytes, sent as the `X-Sentry-Signature` header.
"""
import asyncio
import hashlib
import hmac
import json
from datetime import UTC, datetime
from logging import getLogger

import httpxyz
from confkit.watcher import FileWatcher

from api.config import (
    SENTRY_FLAGS_SIGNING_SECRET,
    SENTRY_FLAGS_WEBHOOK_URL,
    Config,
    FlagTree,
    read_flags,
)

logger = getLogger(__name__)

# A config-file edit has no human author; attribute changes to the app itself.
_CREATED_BY = {"id": "factorio-server-manager", "type": "name"}


def flatten(tree: FlagTree, prefix: str = "") -> dict[str, bool]:
    """Flatten the nested flag tree to dotted leaf keys, e.g. ``Mods.enabled``."""
    out: dict[str, bool] = {}
    for name, value in tree.items():
        key = f"{prefix}{name}"
        if isinstance(value, dict):
            out.update(flatten(value, f"{key}."))
        else:
            out[key] = bool(value)
    return out


def _change_id(flag: str, created_at: str, value: bool | None) -> int:
    """Stable 64-bit idempotency token so a retried POST isn't double-counted."""
    digest = hashlib.sha256(f"{flag}|{created_at}|{value}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def diff(old: dict[str, bool], new: dict[str, bool], created_at: str) -> list[dict]:
    """Build Sentry change objects for flags that were added, removed or toggled."""
    changes: list[dict] = []
    for key in old.keys() | new.keys():
        before, after = old.get(key), new.get(key)
        if before == after:
            continue
        if key not in old:
            action, value = "created", after
        elif key not in new:
            action, value = "deleted", before
        else:
            action, value = "updated", after
        changes.append({
            "action": action,
            "flag": key,
            "created_at": created_at,
            "created_by": _CREATED_BY,
            "change_id": _change_id(key, created_at, value),
        })
    return changes


def build_payload(changes: list[dict]) -> dict:
    """Wrap change objects in the generic-provider envelope."""
    return {"meta": {"version": 1}, "data": changes}


def _sign(body: bytes) -> str:
    """HMAC-SHA256 hex digest of the raw request body, per Sentry's spec."""
    return hmac.new(SENTRY_FLAGS_SIGNING_SECRET.encode(), body, hashlib.sha256).hexdigest()


async def send_flag_changes(changes: list[dict]) -> None:
    """POST signed flag changes to Sentry. Logs failures; never raises to the caller."""
    if not changes:
        return
    body = json.dumps(build_payload(changes)).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Sentry-Signature": _sign(body),
    }
    try:
        async with httpxyz.AsyncClient(timeout=10.0) as client:
            response = await client.post(SENTRY_FLAGS_WEBHOOK_URL, content=body, headers=headers)
        if response.status_code >= 300:
            logger.warning(
                "Sentry flag change webhook returned %s for %d change(s)",
                response.status_code,
                len(changes),
            )
    except Exception:
        logger.exception("Failed to send %d flag change(s) to Sentry", len(changes))


async def watch_flag_changes() -> None:
    """Watch the flags ini and emit change events to Sentry on every real toggle.

    Primes the snapshot and swallows the watcher's initial signal so a restart or
    deploy re-reading the same ini never re-emits — only genuine edits are sent.
    """
    snapshot = flatten(read_flags())
    watcher = FileWatcher(Config._file)  # noqa: SLF001 - our Config subclass owns the ini path
    watcher.has_changed()  # prime: discard the initial True so connect/restart is silent
    logger.info("Sentry flag change tracking active (%d flags)", len(snapshot))
    while True:
        await asyncio.sleep(1.0)
        if not watcher.has_changed():
            continue
        current = flatten(read_flags())
        changes = diff(snapshot, current, datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S"))
        if changes:
            await send_flag_changes(changes)
        snapshot = current
