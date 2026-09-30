from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """Sliding window thread-safe rate limiter.
    
    Returns HTTP 429 with Retry-After header when rate limit is exceeded.
    """

    def __init__(self, requests_limit: int, window_seconds: int = 60) -> None:
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self._records: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = time.time()
        with self._lock:
            # Clean timestamps older than the sliding window
            timestamps = [t for t in self._records[key] if now - t < self.window_seconds]
            if len(timestamps) >= self.requests_limit:
                retry_after = int(self.window_seconds - (now - timestamps[0])) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please wait a moment before trying again.",
                    headers={"Retry-After": str(max(1, retry_after))},
                )
            timestamps.append(now)
            self._records[key] = timestamps

    def __call__(self, request: Request) -> None:
        # Rate limit by client IP (or forwarded header)
        forwarded = request.headers.get("x-forwarded-for")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
        self.check(client_ip)

    def reset(self) -> None:
        """Clear records (useful in tests)."""
        with self._lock:
            self._records.clear()


# Pre-configured rate limiters according to ARCHITECTURE.md specifications
login_rate_limiter = InMemoryRateLimiter(requests_limit=10, window_seconds=60)
translate_rate_limiter = InMemoryRateLimiter(requests_limit=60, window_seconds=60)
