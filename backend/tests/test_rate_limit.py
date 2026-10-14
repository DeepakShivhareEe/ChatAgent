"""
Tests for the rate limiter middleware — per-site budgets and client IP trust.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from starlette.responses import PlainTextResponse

from app.config import settings
from app.security.rate_limiter import RateLimiter


async def _ok(scope, receive, send):
    """Minimal ASGI app so the middleware can be tested without the whole API."""
    await PlainTextResponse("ok")(scope, receive, send)


def _client(max_requests, trust_proxy_headers=False):
    limiter = RateLimiter(
        _ok,
        max_requests=max_requests,
        window_seconds=60,
        trust_proxy_headers=trust_proxy_headers,
    )
    return limiter, AsyncClient(
        transport=ASGITransport(app=limiter), base_url="http://test"
    )


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_site_a_hitting_the_limit_does_not_block_site_b(monkeypatch):
    monkeypatch.setattr(settings, "SITE_TOKENS", "alpha:key-a,beta:key-b")
    limiter, client = _client(max_requests=2)
    async with client:
        for _ in range(2):
            response = await client.get("/chat", headers={"X-Site-Key": "key-a"})
            assert response.status_code == 200
        assert (
            await client.get("/chat", headers={"X-Site-Key": "key-a"})
        ).status_code == 429
        # Site B has its own budget from the same IP.
        assert (
            await client.get("/chat", headers={"X-Site-Key": "key-b"})
        ).status_code == 200


@pytest.mark.anyio
async def test_buckets_are_per_ip_within_a_site(monkeypatch):
    monkeypatch.setattr(settings, "SITE_TOKENS", "alpha:key-a")
    limiter, client = _client(max_requests=1)
    async with client:
        assert (
            await client.get("/chat", headers={"X-Site-Key": "key-a"})
        ).status_code == 200
        assert (
            await client.get("/chat", headers={"X-Site-Key": "key-a"})
        ).status_code == 429


@pytest.mark.anyio
async def test_behaves_as_before_without_site_tokens(monkeypatch):
    monkeypatch.setattr(settings, "SITE_TOKENS", "")
    limiter, client = _client(max_requests=1)
    async with client:
        assert (await client.get("/chat")).status_code == 200
        assert (await client.get("/chat")).status_code == 429
        keys = list(limiter._requests)
        assert keys and all(key.startswith("-|") for key in keys)


@pytest.mark.anyio
async def test_spoofed_forwarded_for_is_ignored_by_default():
    limiter, client = _client(max_requests=1, trust_proxy_headers=False)
    async with client:
        first = await client.get("/chat", headers={"X-Forwarded-For": "1.2.3.4"})
        second = await client.get("/chat", headers={"X-Forwarded-For": "5.6.7.8"})
    assert first.status_code == 200
    assert second.status_code == 429  # same socket address, header ignored


@pytest.mark.anyio
async def test_forwarded_for_is_honoured_when_trusted():
    limiter, client = _client(max_requests=1, trust_proxy_headers=True)
    async with client:
        first = await client.get("/chat", headers={"X-Forwarded-For": "1.2.3.4"})
        same = await client.get("/chat", headers={"X-Forwarded-For": "1.2.3.4"})
        other = await client.get("/chat", headers={"X-Forwarded-For": "5.6.7.8"})
    assert first.status_code == 200
    assert same.status_code == 429
    assert other.status_code == 200


@pytest.mark.anyio
async def test_tracked_buckets_are_capped():
    limiter, client = _client(max_requests=5, trust_proxy_headers=True)
    limiter.MAX_KEYS = 3
    async with client:
        for octet in range(10):
            await client.get(
                "/chat", headers={"X-Forwarded-For": f"10.0.0.{octet}"}
            )
    assert len(limiter._requests) <= 3


@pytest.mark.anyio
async def test_health_and_preflight_are_not_limited():
    limiter, client = _client(max_requests=1)
    async with client:
        assert (await client.get("/health")).status_code == 200
        assert (await client.get("/health")).status_code == 200
        assert (await client.options("/chat")).status_code == 200
        assert (await client.options("/chat")).status_code == 200
    assert len(limiter._requests) == 0
