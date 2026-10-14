"""
Tests for API endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AI Website Assistant API"
    assert "version" in data


@pytest.mark.anyio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.anyio
async def test_chat_empty_query():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/chat", json={"query": ""})
    # Should return 422 validation error (min_length=1)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_search_empty_query(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "test-admin-key")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/search",
            headers={"X-Admin-Key": "test-admin-key"},
            json={"query": ""},
        )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_search_requires_admin_key(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "test-admin-key")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/search",
            json={"query": "pricing", "top_k": 3},
        )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_search_valid(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "test-admin-key")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/search",
            headers={"X-Admin-Key": "test-admin-key"},
            json={"query": "pricing", "top_k": 3},
        )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "query" in data
