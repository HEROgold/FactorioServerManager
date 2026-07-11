"""API router for feature flags: a live snapshot plus an SSE change signal.

Flags are declared once in `api.config.FeatureFlags`; this router just serves
their current values and pings connected clients whenever the ini changes so the
frontend can re-fetch without a restart or page reload.
"""
import asyncio
from typing import TYPE_CHECKING

from confkit.watcher import FileWatcher
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.config import Config, FeatureFlagsModel, FlagTree, read_flags
from api.constants import SSE_HEADERS

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

router = APIRouter()


@router.get("/feature-flags", response_model=FeatureFlagsModel)
async def get_feature_flags() -> FlagTree:
    """Current feature flags (nested). Read live so a post-signal re-fetch is fresh."""
    return read_flags()


@router.get("/feature-flags/stream")
async def feature_flags_stream() -> StreamingResponse:
    """Emit a 'featureFlagsUpdate' event whenever api_config.ini changes; clients re-fetch."""
    async def generate() -> AsyncGenerator[str]:
        watcher = FileWatcher(Config._file)  # noqa: SLF001 - our Config subclass owns the ini path
        watcher.has_changed()  # prime: swallow the initial True so we don't ping on connect
        while True:
            if watcher.has_changed():
                yield "event: featureFlagsUpdate\n"
                yield "data: changed\n\n"
            await asyncio.sleep(1.0)

    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)
