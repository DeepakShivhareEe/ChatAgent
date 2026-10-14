"""
AI Website Assistant — FastAPI Application Entry Point.

A production-ready, provider-agnostic AI chatbot backend with RAG pipeline.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.dependencies import initialize_services, shutdown_services
from app.api.routes import health, chat, ingest, search
from app.security.rate_limiter import RateLimiter
from app.security.headers import SecurityHeadersMiddleware
from app.security.redaction import redact_secrets
from app.security.site_key import enforce_site_tokens_configured
from app.models.exceptions import AppException

# --- Logging ---
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class _RedactSecretsFilter(logging.Filter):
    """Strip credential-looking text from every log record before it is written."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(
                redact_secrets(arg) if isinstance(arg, str) else arg
                for arg in record.args
            )
        elif isinstance(record.args, dict):
            record.args = {
                key: (redact_secrets(value) if isinstance(value, str) else value)
                for key, value in record.args.items()
            }
        return True


# basicConfig created the root handler; filter at the handler so records from
# every logger (including uvicorn's child loggers) are redacted.
for _handler in logging.getLogger().handlers:
    _handler.addFilter(_RedactSecretsFilter())


# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, cleanup on shutdown."""
    logger.info("=" * 60)
    logger.info("AI Website Assistant — Starting up")
    logger.info(f"Provider: {settings.AI_PROVIDER} | Model: {settings.MODEL_NAME}")
    logger.info("=" * 60)
    # Fails fast in production (DEBUG=false) when SITE_TOKENS is empty, before
    # any model or vector store is loaded.
    enforce_site_tokens_configured()
    await initialize_services()
    yield
    await shutdown_services()
    logger.info("AI Website Assistant — Shut down")


# --- App ---
# Docs *and* the raw schema are gated together: leaving openapi_url enabled
# would still serve /openapi.json (with the full route list) when docs are off.
app = FastAPI(
    title="AI Website Assistant API",
    description=(
        "A production-ready AI chatbot backend with RAG pipeline. "
        "Integrates into any website to answer questions from the knowledge base."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.EXPOSE_API_DOCS else None,
    redoc_url="/redoc" if settings.EXPOSE_API_DOCS else None,
    openapi_url="/openapi.json" if settings.EXPOSE_API_DOCS else None,
)


# --- Middleware ---

# Rate limiting — one budget per (site, client IP)
app.add_middleware(
    RateLimiter,
    max_requests=settings.RATE_LIMIT,
    window_seconds=60,
    trust_proxy_headers=settings.TRUST_PROXY_HEADERS,
)
app.add_middleware(SecurityHeadersMiddleware, max_request_bytes=settings.MAX_REQUEST_BYTES)

# CORS — explicit allowlists (no wildcards). The widget sends a custom
# `X-Site-Key` header, so browsers issue a preflight OPTIONS request before
# POST /chat; both the header and the POST method must be allowed here or the
# browser blocks every chat request.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Site-Key"],
)


# --- Exception handlers ---
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions.

    The client only sees ``exc.client_message``: 4xx messages are written for
    the user, while 5xx messages stay in the server log. Upstream text and file
    paths must not reach the browser.
    """
    if exc.status_code >= 500:
        logger.error(
            "Application error %s on %s: %s",
            exc.status_code,
            request.url.path,
            redact_secrets(exc.message),
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.client_message},
    )


# --- Routes ---
app.include_router(health.router, prefix="", tags=["Health"])
app.include_router(chat.router, prefix="", tags=["Chat"])
app.include_router(ingest.router, prefix="", tags=["Knowledge Base"])
app.include_router(search.router, prefix="", tags=["Search"])


# --- Root ---
@app.get("/", tags=["Root"])
async def root():
    """API root — basic info."""
    return {
        "name": "AI Website Assistant API",
        "version": "1.0.0",
        "docs": "/docs" if settings.EXPOSE_API_DOCS else None,
        "health": "/health",
    }
