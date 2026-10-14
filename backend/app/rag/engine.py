"""
RAG Engine — orchestrates the full retrieval-augmented generation pipeline.
"""

import uuid
import logging
from typing import AsyncGenerator

from app.providers.base import LLMProvider
from app.rag.retriever import Retriever
from app.rag.prompt import PromptBuilder
from app.security.sanitizer import Sanitizer
from app.security.injection import InjectionDetector

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Orchestrates the RAG pipeline:
    1. Sanitize and validate input
    2. Detect prompt injection
    3. Retrieve relevant context
    4. Build context-aware prompt
    5. Generate response via LLM provider
    """

    def __init__(
        self,
        provider: LLMProvider,
        retriever: Retriever,
        prompt_builder: PromptBuilder,
        sanitizer: Sanitizer,
        injection_detector: InjectionDetector,
    ):
        self.provider = provider
        self.retriever = retriever
        self.prompt_builder = prompt_builder
        self.sanitizer = sanitizer
        self.injection_detector = injection_detector

    async def query(
        self,
        user_query: str,
        conversation_history: list[dict] | None = None,
        conversation_id: str | None = None,
    ) -> dict:
        """
        Process a user query through the full RAG pipeline (non-streaming).

        Returns:
            dict with 'answer', 'sources', 'conversation_id'.
        """
        # Sanitize input
        clean_query = self.sanitizer.sanitize_input(user_query)

        # Check for injection
        self.injection_detector.detect(clean_query)

        # Generate conversation ID
        conv_id = conversation_id or str(uuid.uuid4())

        # Retrieve relevant context
        context_chunks = await self.retriever.retrieve(clean_query)
        logger.info(
            f"Retrieved {len(context_chunks)} relevant chunks for query: "
            f"'{clean_query[:80]}...'"
        )

        # Check if we have relevant context
        if not context_chunks:
            return {
                "answer": self.prompt_builder.fallback_response,
                "sources": [],
                "conversation_id": conv_id,
            }

        # Build prompt with context
        messages = self.prompt_builder.build_messages(
            query=clean_query,
            context_chunks=context_chunks,
            conversation_history=conversation_history,
        )

        # Generate response
        answer = await self.provider.generate(messages)

        # Sanitize output
        clean_answer = self.sanitizer.sanitize_output(answer)

        # Extract source names
        sources = list({
            chunk.get("metadata", {}).get("source", "Unknown")
            for chunk in context_chunks
        })

        return {
            "answer": clean_answer,
            "sources": sources,
            "conversation_id": conv_id,
        }

    async def query_stream(
        self,
        user_query: str,
        conversation_history: list[dict] | None = None,
        conversation_id: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Process a user query through the RAG pipeline with streaming.

        Yields:
            dicts with 'type' and 'content' for SSE events.
        """
        # Sanitize input
        clean_query = self.sanitizer.sanitize_input(user_query)

        # Check for injection
        self.injection_detector.detect(clean_query)

        # Generate conversation ID
        conv_id = conversation_id or str(uuid.uuid4())

        # Send conversation ID
        yield {"type": "meta", "conversation_id": conv_id}

        # Retrieve relevant context
        context_chunks = await self.retriever.retrieve(clean_query)
        logger.info(
            f"Retrieved {len(context_chunks)} relevant chunks for streaming query"
        )

        # Check if we have relevant context
        if not context_chunks:
            yield {
                "type": "content",
                "content": self.prompt_builder.fallback_response,
            }
            yield {"type": "sources", "sources": []}
            yield {"type": "done"}
            return

        # Build prompt with context
        messages = self.prompt_builder.build_messages(
            query=clean_query,
            context_chunks=context_chunks,
            conversation_history=conversation_history,
        )

        # Stream response. Hold back a small tail between chunks so a
        # dangerous tag/link split across a chunk boundary is sanitized as a
        # whole instead of slipping through in fragments.
        buffer = ""
        async for chunk in self.provider.generate_stream(messages):
            buffer += chunk
            emit, buffer = self.sanitizer.stream_split(buffer)
            if emit:
                sanitized = self.sanitizer.sanitize_output(emit)
                if sanitized:
                    yield {"type": "content", "content": sanitized}

        # Flush whatever is still buffered when the provider stream ends.
        if buffer:
            sanitized = self.sanitizer.sanitize_output(buffer)
            if sanitized:
                yield {"type": "content", "content": sanitized}

        # Send sources
        sources = list({
            chunk.get("metadata", {}).get("source", "Unknown")
            for chunk in context_chunks
        })
        yield {"type": "sources", "sources": sources}
        yield {"type": "done"}
