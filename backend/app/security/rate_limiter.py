"""
Rate limiter middleware — sliding window rate limiting per site and IP address.
"""

import time
import logging
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.security.site_key import site_for_token

logger = logging.getLogger(__name__)


class RateLimiter(BaseHTTPMiddleware):
    """Sliding window rate limiter keyed on (site, client IP).

    When `SITE_TOKENS` is configured, each site gets its own budget so one busy
    site cannot exhaust the limit for the others. With no tokens configured the
    site part is empty and the behaviour is the per-IP limit as before.
    """

    #: Hard cap on the number of buckets tracked at once, so a flood of distinct
    #: keys cannot grow memory without bound inside a window. The stalest keys
    #: are evicted first.
    MAX_KEYS = 10_000

    def __init__(
        self,
        app,
        max_requests: int = 30,
        window_seconds: int = 60,
        trust_proxy_headers: bool = False,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.trust_proxy_headers = trust_proxy_headers
        # bucket key -> list of request timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._last_global_cleanup = 0.0

    def _get_client_ip(self, request: Request) -> str:
        """Client IP, using X-Forwarded-For only when it is trusted.

        `X-Forwarded-For` is client-controlled unless a reverse proxy overwrites
        it, so it is ignored by default. When TRUST_PROXY_HEADERS is enabled the
        first (left-most) value is the original client as seen by the proxy.
        """
        if self.trust_proxy_headers:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                first = forwarded.split(",")[0].strip()
                if first:
                    return first
        return request.client.host if request.client else "unknown"

    def _get_bucket_key(self, request: Request) -> str:
        """Bucket on (site, IP) so each site has its own allowance."""
        site = site_for_token(request.headers.get("x-site-key")) or "-"
        return f"{site}|{self._get_client_ip(request)}"

    def _cleanup(self, key: str, now: float) -> None:
        """Remove expired entries for a bucket."""
        cutoff = now - self.window_seconds
        self._requests[key] = [
            ts for ts in self._requests[key] if ts > cutoff
        ]
        # Remove empty entries to prevent memory leak
        if not self._requests[key]:
            del self._requests[key]

    def _cleanup_all(self, now: float) -> None:
        if now - self._last_global_cleanup < self.window_seconds:
            return
        self._last_global_cleanup = now
        for key in list(self._requests):
            self._cleanup(key, now)

    def _enforce_key_cap(self) -> None:
        """Evict the stalest buckets when too many are tracked at once."""
        excess = len(self._requests) - self.MAX_KEYS
        if excess <= 0:
            return
        stalest = sorted(self._requests, key=lambda key: self._requests[key][-1])
        for key in stalest[:excess]:
            del self._requests[key]

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks
        if request.method == "OPTIONS" or request.url.path == "/health":
            return await call_next(request)

        key = self._get_bucket_key(request)
        now = time.time()
        self._cleanup_all(now)

        # Cleanup old entries
        self._cleanup(key, now)

        # Check rate limit
        request_count = len(self._requests.get(key, []))
        if request_count >= self.max_requests:
            self._enforce_key_cap()
            logger.warning(f"Rate limit exceeded for bucket: {key}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": self.window_seconds,
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        # Record request. Enforcing the cap afterwards keeps the tracked count
        # at or below MAX_KEYS; the bucket just written holds the newest
        # timestamp, so eviction (stalest first) never removes it.
        self._requests[key].append(now)
        self._enforce_key_cap()

        return await call_next(request)
