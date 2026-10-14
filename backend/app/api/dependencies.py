"""
Dependency injection for FastAPI routes.
Provides singleton instances of core services.
"""

import logging
from functools import lru_cache

from app.config import settings
from app.providers.factory import get_provider
from app.providers.base import LLMProvider
from app.ingestion.embeddings import EmbeddingService
from app.vectordb.chromadb import ChromaDBClient
from app.rag.retriever import Retriever
from app.rag.prompt import PromptBuilder
from app.rag.engine import RAGEngine
from app.ingestion.pipeline import IngestionPipeline
from app.security.sanitizer import Sanitizer
from app.security.injection import InjectionDetector
from app.conversation.store import ConversationStore

logger = logging.getLogger(__name__)

# --- Singletons (initialized lazily) ---

_embedding_service: EmbeddingService | None = None
_db_client: ChromaDBClient | None = None
_provider: LLMProvider | None = None
_rag_engine: RAGEngine | None = None
_ingestion_pipeline: IngestionPipeline | None = None
_sanitizer: Sanitizer | None = None
_injection_detector: InjectionDetector | None = None
_conversation_store: ConversationStore | None = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL)
    return _embedding_service


def get_db_client() -> ChromaDBClient:
    """Get or create the ChromaDB client singleton."""
    global _db_client
    if _db_client is None:
        _db_client = ChromaDBClient(
            persist_directory=settings.VECTOR_DB_PATH,
            collection_name=settings.COLLECTION_NAME,
            embedding_service=get_embedding_service(),
        )
    return _db_client


def get_llm_provider() -> LLMProvider:
    """Get or create the LLM provider singleton."""
    global _provider
    if _provider is None:
        _provider = get_provider(
            provider_name=settings.AI_PROVIDER,
            api_key=settings.API_KEY,
            model=settings.MODEL_NAME,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
            top_p=settings.TOP_P,
        )
        logger.info(
            f"LLM provider initialized: {settings.AI_PROVIDER} ({settings.MODEL_NAME})"
        )
    return _provider


def get_sanitizer() -> Sanitizer:
    """Get or create the sanitizer singleton."""
    global _sanitizer
    if _sanitizer is None:
        _sanitizer = Sanitizer()
    return _sanitizer


def get_injection_detector() -> InjectionDetector:
    """Get or create the injection detector singleton."""
    global _injection_detector
    if _injection_detector is None:
        _injection_detector = InjectionDetector()
    return _injection_detector


def get_rag_engine() -> RAGEngine:
    """Get or create the RAG engine singleton."""
    global _rag_engine
    if _rag_engine is None:
        db_client = get_db_client()
        retriever = Retriever(
            db_client=db_client,
            top_k=settings.TOP_K,
            similarity_threshold=settings.SIMILARITY_THRESHOLD,
        )
        prompt_builder = PromptBuilder(
            website_name=settings.WEBSITE_NAME,
            assistant_name=settings.ASSISTANT_NAME,
        )
        _rag_engine = RAGEngine(
            provider=get_llm_provider(),
            retriever=retriever,
            prompt_builder=prompt_builder,
            sanitizer=get_sanitizer(),
            injection_detector=get_injection_detector(),
        )
    return _rag_engine


def get_ingestion_pipeline() -> IngestionPipeline:
    """Get or create the ingestion pipeline singleton."""
    global _ingestion_pipeline
    if _ingestion_pipeline is None:
        _ingestion_pipeline = IngestionPipeline(
            db_client=get_db_client(),
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            max_file_bytes=settings.MAX_INGEST_FILE_BYTES,
            max_files=settings.MAX_INGEST_FILES,
        )
    return _ingestion_pipeline


def get_conversation_store() -> ConversationStore:
    global _conversation_store
    if _conversation_store is None:
        _conversation_store = ConversationStore(
            window=settings.CONVERSATION_WINDOW,
            ttl_seconds=settings.CONVERSATION_TTL_SECONDS,
            max_conversations=settings.MAX_CONVERSATIONS,
        )
    return _conversation_store


async def initialize_services() -> None:
    """Initialize all services on startup."""
    logger.info("Initializing services...")
    get_embedding_service()
    get_db_client()
    get_llm_provider()
    get_rag_engine()
    get_ingestion_pipeline()
    get_conversation_store()
    logger.info("All services initialized successfully")


async def shutdown_services() -> None:
    """Cleanup on shutdown."""
    global _embedding_service, _db_client, _provider, _rag_engine
    global _ingestion_pipeline, _sanitizer, _injection_detector, _conversation_store
    _embedding_service = None
    _db_client = None
    _provider = None
    _rag_engine = None
    _ingestion_pipeline = None
    _sanitizer = None
    _injection_detector = None
    _conversation_store = None
    logger.info("Services shut down")
