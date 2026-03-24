"""Rate limiting middleware and utilities."""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import settings


class RateLimitStore:
    """In-memory rate limit store."""

    def __init__(self) -> None:
        """Initialize rate limit store."""
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._operation_cooldowns: dict[str, float] = {}

    def check_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if rate limit is exceeded."""
        now = time.time()
        window_start = now - window_seconds

        # Clean old requests
        self._requests[key] = [req_time for req_time in self._requests[key] if req_time > window_start]

        # Check limit
        if len(self._requests[key]) >= max_requests:
            return False

        # Add current request
        self._requests[key].append(now)
        return True

    def get_retry_after(self, key: str, window_seconds: int) -> int:
        """Get seconds until rate limit resets."""
        if not self._requests[key]:
            return 0
        oldest = min(self._requests[key])
        retry_after = int((oldest + window_seconds) - time.time())
        return max(0, retry_after)

    def check_operation_cooldown(self, user_id: int, operation: str) -> tuple[bool, int]:
        """Check if operation is in cooldown.

        Returns:
            tuple[bool, int]: (is_allowed, seconds_remaining)
        """
        key = f"{user_id}:{operation}"
        now = time.time()

        if key in self._operation_cooldowns:
            cooldown_until = self._operation_cooldowns[key]
            if now < cooldown_until:
                seconds_remaining = int(cooldown_until - now)
                return False, seconds_remaining

        return True, 0

    def set_operation_cooldown(self, user_id: int, operation: str, cooldown_seconds: int) -> None:
        """Set cooldown for an operation."""
        key = f"{user_id}:{operation}"
        self._operation_cooldowns[key] = time.time() + cooldown_seconds

    def clear_old_cooldowns(self) -> None:
        """Clear expired cooldowns."""
        now = time.time()
        expired_keys = [key for key, cooldown_until in self._operation_cooldowns.items() if cooldown_until < now]
        for key in expired_keys:
            del self._operation_cooldowns[key]


rate_limit_store = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"
        rate_limit_key = f"ip:{client_ip}"

        # Check rate limit (60 requests per minute)
        if not rate_limit_store.check_rate_limit(rate_limit_key, settings.RATE_LIMIT_PER_MINUTE, 60):
            retry_after = rate_limit_store.get_retry_after(rate_limit_key, 60)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)


def require_operation_cooldown(user_id: int, operation: str) -> None:
    """Check operation cooldown and raise exception if in cooldown."""
    is_allowed, seconds_remaining = rate_limit_store.check_operation_cooldown(user_id, operation)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Operation on cooldown. Try again in {seconds_remaining} seconds.",
            headers={"Retry-After": str(seconds_remaining)},
        )


def set_operation_cooldown(user_id: int, operation: str) -> None:
    """Set cooldown for heavy operation."""
    rate_limit_store.set_operation_cooldown(user_id, operation, settings.SERVER_OPERATION_COOLDOWN_SECONDS)
