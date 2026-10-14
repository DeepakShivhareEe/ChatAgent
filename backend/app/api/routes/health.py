"""
Health and status endpoints.
"""

from fastapi import APIRouter, Depends
from app.config import settings
from app.models.schemas import HealthResponse, StatusResponse
from app.api.dependencies import get_db_client
from app.security.admin import verify_admin_key

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@router.get("/status", response_model=StatusResponse, tags=["Health"])
async def status(_: None = Depends(verify_admin_key)):
    """Detailed status with provider, model, and vector DB info."""
    db_client = get_db_client()
    db_stats = db_client.get_stats()

    import os
    knowledge_dir = settings.KNOWLEDGE_DIRECTORY
    knowledge_files = 0
    if os.path.isdir(knowledge_dir):
        for root, _, files in os.walk(knowledge_dir):
            knowledge_files += len(files)

    return StatusResponse(
        status="healthy",
        version="1.0.0",
        provider=settings.AI_PROVIDER,
        model=settings.MODEL_NAME,
        vector_db={
            "type": "chromadb",
            "collection": db_stats["collection_name"],
            "document_count": db_stats["document_count"],
        },
        knowledge_base={
            "directory": knowledge_dir,
            "file_count": knowledge_files,
        },
    )
