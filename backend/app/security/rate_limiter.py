"""
Rate limiter middleware — sliding window rate limiting by IP address.
"""

import time
import logging
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimiter(BaseHTTPMiddleware):
    """Sliding window rate limiter middleware."""

    def __init__(self, app, max_requests: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # IP -> list of request timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._last_global_cleanup = 0.0

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Do not trust client-supplied X-Forwarded-For. Configure proxy-header
        # handling at the trusted reverse proxy / Uvicorn boundary instead.
        return request.client.host if request.client else "unknown"

    def _cleanup(self, ip: str, now: float) -> None:
        """Remove expired entries for an IP."""
        cutoff = now - self.window_seconds
        self._requests[ip] = [
            ts for ts in self._requests[ip] if ts > cutoff
        ]
        # Remove empty entries to prevent memory leak
        if not self._requests[ip]:
            del self._requests[ip]

    def _cleanup_all(self, now: float) -> None:
        if now - self._last_global_cleanup < self.window_seconds:
            return
        self._last_global_cleanup = now
        for ip in list(self._requests):
            self._cleanup(ip, now)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks
        if request.method == "OPTIONS" or request.url.path == "/health":
            return await call_next(request)

        ip = self._get_client_ip(request)
        now = time.time()
        self._cleanup_all(now)

        # Cleanup old entries
        self._cleanup(ip, now)

        # Check rate limit
        request_count = len(self._requests.get(ip, []))
        if request_count >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": self.window_seconds,
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        # Record request
        self._requests[ip].append(now)

        return await call_next(request)
