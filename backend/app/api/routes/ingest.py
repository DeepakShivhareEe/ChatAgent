"""
Ingest endpoint — triggers document ingestion pipeline.
Protected by admin API key when configured.
"""

import logging

from fastapi import APIRouter, Header, HTTPException
from typing import Optional

from app.config import settings
from app.security.admin import verify_admin_key
from app.models.schemas import IngestRequest, IngestResponse
from app.api.dependencies import get_ingestion_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/ingest", response_model=IngestResponse, tags=["Knowledge Base"])
async def ingest_documents(
    request: IngestRequest = IngestRequest(),
    x_admin_key: Optional[str] = Header(default=None),
):
    """
    Trigger document ingestion from the knowledge directory.

    Scans the configured knowledge directory (or a custom directory),
    loads all supported files, chunks them, generates embeddings,
    and stores them in the vector database.

    Requires the `X-Admin-Key` header if `ADMIN_API_KEY` is configured.
    """
    # Verify admin key
    verify_admin_key(x_admin_key)

    pipeline = get_ingestion_pipeline()
    if request.directory and not settings.ALLOW_CUSTOM_INGEST_DIRECTORY:
        raise HTTPException(
            status_code=400,
            detail="Custom ingestion directories are disabled. Use KNOWLEDGE_DIRECTORY.",
        )
    directory = request.directory or settings.KNOWLEDGE_DIRECTORY

    logger.info(f"Starting ingestion from: {directory}")

    stats = await pipeline.ingest(
        directory=directory,
        clear_existing=request.clear_existing,
    )

    return IngestResponse(
        status="completed",
        documents_processed=stats["documents_processed"],
        chunks_created=stats["chunks_created"],
        errors=stats["errors"],
    )
