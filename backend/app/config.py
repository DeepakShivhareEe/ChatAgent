"""
Application configuration loaded from environment variables.
Uses Pydantic BaseSettings for validation and type coercion.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """All application configuration — loaded from environment variables."""

    # --- AI Provider ---
    AI_PROVIDER: str = Field(
        default="openai",
        description="LLM provider: openai | anthropic | gemini | groq | openrouter",
    )
    API_KEY: str = Field(
        default="",
        description="API key for the selected LLM provider",
    )
    MODEL_NAME: str = Field(
        default="gpt-4o-mini",
        description="Model name for the selected provider",
    )
    TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="LLM temperature (lower = more deterministic)",
    )
    MAX_TOKENS: int = Field(
        default=1024,
        ge=1,
        le=128000,
        description="Maximum tokens in LLM response",
    )
    TOP_P: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Top-p sampling parameter",
    )

    # --- Embeddings ---
    EMBEDDING_MODEL: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence-transformers model for embeddings",
    )

    # --- Vector Database ---
    VECTOR_DB_PATH: str = Field(
        default="./data/chromadb",
        description="Path for ChromaDB persistent storage",
    )
    COLLECTION_NAME: str = Field(
        default="website_knowledge",
        description="ChromaDB collection name",
    )

    # --- Knowledge Base ---
    KNOWLEDGE_DIRECTORY: str = Field(
        default="./knowledge",
        description="Directory containing knowledge base documents",
    )

    # --- Chunking ---
    CHUNK_SIZE: int = Field(
        default=512,
        ge=100,
        le=8000,
        description="Maximum characters per text chunk",
    )
    CHUNK_OVERLAP: int = Field(
        default=50,
        ge=0,
        le=500,
        description="Character overlap between consecutive chunks",
    )

    # --- RAG ---
    TOP_K: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of top results to retrieve from vector search",
    )
    SIMILARITY_THRESHOLD: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score to include a result",
    )

    # --- Conversation ---
    CONVERSATION_WINDOW: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of previous messages to include for multi-turn context",
    )
    CONVERSATION_TTL_SECONDS: int = Field(default=3600, ge=60, le=86400)
    MAX_CONVERSATIONS: int = Field(default=10000, ge=1, le=100000)

    # --- Security ---
    ADMIN_API_KEY: str = Field(
        default="",
        description="API key required for admin endpoints (ingest is disabled when empty)",
    )
    RATE_LIMIT: int = Field(
        default=30,
        ge=1,
        description="Maximum requests per minute per IP",
    )
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated allowed CORS origins",
    )
    ALLOW_CUSTOM_INGEST_DIRECTORY: bool = Field(
        default=False,
        description="Allow an admin to ingest a directory other than KNOWLEDGE_DIRECTORY",
    )
    MAX_INGEST_FILE_BYTES: int = Field(default=10_000_000, ge=1024, le=1_000_000_000)
    MAX_INGEST_FILES: int = Field(default=1000, ge=1, le=100_000)
    MAX_REQUEST_BYTES: int = Field(default=100_000, ge=1024, le=10_000_000)
    EXPOSE_API_DOCS: bool = Field(default=False)

    # --- Server ---
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # --- Website Info ---
    WEBSITE_NAME: str = Field(
        default="Our Website",
        description="Name of the website this assistant serves",
    )
    ASSISTANT_NAME: str = Field(
        default="AI Assistant",
        description="Display name of the assistant",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        if "*" in origins and not self.DEBUG:
            raise ValueError("CORS_ORIGINS cannot contain '*' when DEBUG is false.")
        return origins

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Singleton instance
settings = Settings()
