"""
Pydantic models for API request/response schemas.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID


# --- Enums ---

# --- Chat ---


class ChatRequest(BaseModel):
    """Request body for POST /chat."""
    model_config = ConfigDict(extra="forbid")
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question",
    )
    conversation_id: Optional[UUID] = Field(
        default=None,
        description="Optional conversation ID for multi-turn context",
    )


class ChatResponse(BaseModel):
    """Non-streaming response for POST /chat."""
    answer: str
    sources: list[str] = Field(default_factory=list)
    conversation_id: str


# --- Search ---

class SearchRequest(BaseModel):
    """Request body for POST /search."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query",
    )
    top_k: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of results to return",
    )


class SearchResult(BaseModel):
    """A single search result."""
    content: str
    source: str
    score: float
    metadata: dict = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Response for POST /search."""
    results: list[SearchResult]
    query: str
    total: int


# --- Ingest ---

class IngestRequest(BaseModel):
    """Request body for POST /ingest."""
    directory: Optional[str] = Field(
        default=None,
        description="Directory to ingest (defaults to KNOWLEDGE_DIRECTORY)",
    )
    clear_existing: bool = Field(
        default=False,
        description="Clear existing vectors before ingesting",
    )


class IngestResponse(BaseModel):
    """Response for POST /ingest."""
    status: str
    documents_processed: int
    chunks_created: int
    errors: list[str] = Field(default_factory=list)


# --- Health ---

class HealthResponse(BaseModel):
    """Response for GET /health."""
    status: str = "healthy"
    version: str = "1.0.0"


class StatusResponse(BaseModel):
    """Response for GET /status."""
    status: str = "healthy"
    version: str = "1.0.0"
    provider: str
    model: str
    vector_db: dict
    knowledge_base: dict
