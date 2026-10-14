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


class _FakeVectorDB:
    """In-memory stand-in for ChromaDBClient: no embedding model, no disk access."""

    async def query(self, query_text, n_results=5):
        return [
            {
                "content": "Pro plan costs $29/month.",
                "metadata": {"source": "pricing.md", "chunk_index": 0},
                "distance": 0.12,
            }
        ]


@pytest.fixture
def fake_db_client(monkeypatch):
    """Patch the vector store so /search never loads a model or touches backend/data."""
    fake = _FakeVectorDB()
    monkeypatch.setattr("app.api.routes.search.get_db_client", lambda: fake)
    return fake


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
async def test_openapi_schema_follows_expose_api_docs():
    """EXPOSE_API_DOCS=False must hide /openapi.json, not just /docs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/openapi.json")
    assert response.status_code == (200 if settings.EXPOSE_API_DOCS else 404)


@pytest.mark.anyio
async def test_chat_empty_query():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/chat", json={"query": ""})
    # Should return 422 validation error (min_length=1)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_chat_missing_site_key_is_unauthorized(monkeypatch):
    monkeypatch.setattr(settings, "SITE_TOKENS", "acme:secret-token")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/chat", json={"query": "hello"})
    assert response.status_code == 401


@pytest.mark.anyio
async def test_chat_invalid_site_key_is_unauthorized(monkeypatch):
    monkeypatch.setattr(settings, "SITE_TOKENS", "acme:secret-token")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/chat",
            headers={"X-Site-Key": "wrong-token"},
            json={"query": "hello"},
        )
    assert response.status_code == 401


class _FakeRAGEngine:
    """Yields one complete turn so /chat can stream without a provider or model."""

    async def query_stream(self, user_query, conversation_history, conversation_id):
        yield {"type": "meta", "conversation_id": conversation_id or "conv-1"}
        yield {"type": "content", "content": "Hello from the assistant"}
        yield {"type": "done"}


@pytest.mark.anyio
async def test_chat_site_key_bound_to_matching_origin_is_allowed(monkeypatch):
    monkeypatch.setattr(settings, "SITE_TOKENS", "acme:secret-token:https://acme.com")
    monkeypatch.setattr("app.api.routes.chat.get_rag_engine", lambda: _FakeRAGEngine())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/chat",
            headers={"X-Site-Key": "secret-token", "Origin": "https://acme.com"},
            json={"query": "hello"},
        )
    assert response.status_code == 200
    assert "Hello from the assistant" in response.text


@pytest.mark.anyio
async def test_chat_site_key_bound_to_other_origin_is_forbidden(monkeypatch):
    monkeypatch.setattr(settings, "SITE_TOKENS", "acme:secret-token:https://acme.com")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/chat",
            headers={"X-Site-Key": "secret-token", "Origin": "https://copycat.example"},
            json={"query": "hello"},
        )
    assert response.status_code == 403


# --- CORS preflight ---
# The widget sends `X-Site-Key`, so the browser preflights POST /chat first.

def _allowed_origin() -> str:
    """First configured origin (the middleware binds CORS_ORIGINS at import)."""
    origins = settings.cors_origins_list
    assert origins, "CORS_ORIGINS must be configured for the preflight tests."
    return origins[0]


@pytest.mark.anyio
async def test_cors_preflight_allows_chat_headers():
    origin = _allowed_origin()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/chat",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "x-site-key,content-type",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    allowed_headers = response.headers["access-control-allow-headers"].lower()
    assert "x-site-key" in allowed_headers
    assert "content-type" in allowed_headers
    assert "post" in response.headers["access-control-allow-methods"].lower()


@pytest.mark.anyio
async def test_cors_preflight_rejects_disallowed_origin():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/chat",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "x-site-key,content-type",
            },
        )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.anyio
async def test_cors_preflight_rejects_unlisted_header():
    origin = _allowed_origin()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/chat",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "x-site-key,x-unlisted-header",
            },
        )
    assert response.status_code == 400
    assert "x-unlisted-header" not in response.headers.get(
        "access-control-allow-headers", ""
    ).lower()


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
async def test_search_valid(monkeypatch, fake_db_client):
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
    assert data["total"] == 1
    assert data["results"][0]["source"] == "pricing.md"
