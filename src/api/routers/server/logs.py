"""Server log API routes (one-shot tail + live SSE streaming)."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from api._types.database import User
from api.constants import SSE_HEADERS
from api.deps import get_current_user
from api.routers.server.shared import _get_server_or_404

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from pathlib import Path

router = APIRouter()

LOG_TAIL_BYTES = 200_000


def _read_log_tail(log_path: Path, limit: int = LOG_TAIL_BYTES) -> str:
    """Return the tail of a log file while keeping huge files manageable."""
    if log_path.is_symlink() or not log_path.is_file():
        return ""
    size = log_path.stat().st_size
    with log_path.open("rb") as handle:
        if limit and size > limit:
            handle.seek(size - limit)
        raw = handle.read()
    return raw.decode("utf-8", errors="replace")


@router.get("/server/{name}/logs")
async def get_logs(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Return current and previous logs (tail-limited) for the named server."""
    server = _get_server_or_404(current_user, name)
    return {
        "current_log": _read_log_tail(server.files.current_log),
        "previous_log": _read_log_tail(server.files.previous_log),
    }


def _stat_for_tail(log_path: Path) -> int | None:
    """Return ``log_path``'s size, or None if it's missing/not a regular file."""
    try:
        if log_path.is_symlink() or not log_path.is_file():
            return None
        return log_path.stat().st_size
    except OSError:
        return None


def _read_new_chunk(log_path: Path, last_size: int) -> tuple[str, int] | None:
    """Read newly-appended log text since ``last_size``, or None on failure.

    Isolates every risky filesystem call behind a narrow ``try``/``except
    OSError`` so the caller's loop stays flat and easy to follow.
    """
    size = _stat_for_tail(log_path)
    if size is None:
        return None
    if size < last_size:
        # File was rotated/truncated; re-read from the start.
        last_size = 0
    if size <= last_size:
        return "", last_size

    try:
        with log_path.open("r", encoding="utf-8", errors="replace") as handle:  # skylos: ignore -- symlink/regular-file checked in _stat_for_tail above
            handle.seek(last_size)
            chunk = handle.read()
            new_size = handle.tell()
    except OSError:
        return None
    else:
        return chunk, new_size


@router.get("/server/{name}/logs/stream")
async def logs_stream(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """Live-tail the current log file as a Server-Sent-Events stream."""
    server = _get_server_or_404(current_user, name)
    log_path = server.files.current_log

    async def generate() -> AsyncGenerator[str]:
        # Start from the end of the file; the frontend seeds its own backlog via
        # the one-shot /logs endpoint, so here we only emit newly appended lines.
        last_size = log_path.stat().st_size if log_path.is_file() else 0
        while True:
            result = _read_new_chunk(log_path, last_size)
            if result is None:
                await asyncio.sleep(1.0)
                continue
            chunk, last_size = result
            if not chunk:
                await asyncio.sleep(0.5)
                continue
            for line in chunk.splitlines():
                yield f"data: {line}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)
