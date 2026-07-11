"""Minimal in-process rate limiter.

A dependency-free sliding-window counter keyed by an arbitrary string (usually
the client IP). It is intentionally small: it guards brute-force amplification
on sensitive endpoints (e.g. login, which relays credentials to Factorio's auth
service) without pulling in a full rate-limiting stack. State is per-process, so
it resets on restart and is not shared across replicas — adequate as a
first-line abuse brake, not a distributed quota.
"""

from __future__ import annotations

import threading
import time
from collections import deque

_WINDOWS: dict[tuple[str, str], deque[float]] = {}
_LOCK = threading.Lock()


def is_rate_limited(key: str, *, limit: int, window_seconds: float, bucket: str = "default") -> bool:
    """Record a hit for ``key`` and report whether it now exceeds ``limit``.

    Returns ``True`` when more than ``limit`` hits have occurred within the last
    ``window_seconds`` (i.e. the caller should reject the request).
    """
    now = time.monotonic()
    cutoff = now - window_seconds
    slot = (bucket, key)
    with _LOCK:
        hits = _WINDOWS.setdefault(slot, deque())
        while hits and hits[0] < cutoff:
            hits.popleft()
        hits.append(now)
        return len(hits) > limit
