"""
Chat endpoint — streaming RAG responses via Server-Sent Events.
"""

import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest
from app.models.exceptions import AppException
from app.rag.engine import RAGEngine
from app.api.dependencies import get_conversation_store, get_injection_detector, get_rag_engine, get_sanitizer

logger = logging.getLogger(__name__)

router = APIRouter()


async def _sse_stream(rag_engine: RAGEngine, request: ChatRequest, http_request: Request):
    """Generate SSE event stream from RAG engine."""
    try:
        clean_query = get_sanitizer().sanitize_input(request.query)
        get_injection_detector().detect(clean_query)
        conversation_id = str(request.conversation_id) if request.conversation_id else None
        store = get_conversation_store()
        history = store.history(conversation_id) if conversation_id else []
        answer_parts: list[str] = []

        async for event in rag_engine.query_stream(
            user_query=clean_query,
            conversation_history=history,
            conversation_id=conversation_id,
        ):
            if await http_request.is_disconnected():
                logger.info("Client disconnected from chat stream")
                return
            if event.get("type") == "meta":
                conversation_id = event["conversation_id"]
            elif event.get("type") == "content":
                answer_parts.append(event.get("content", ""))
            elif event.get("type") == "done" and conversation_id:
                # Persist only completed turns. A provider failure or client
                # disconnect cannot leave an unpaired user message in history.
                store.append(conversation_id, "user", clean_query)
                store.append(conversation_id, "assistant", "".join(answer_parts))
            event_type = event.get("type", "content")
            data = json.dumps(event, ensure_ascii=False)
            yield f"event: {event_type}\ndata: {data}\n\n"

    except AppException as e:
        error_event = json.dumps({
            "type": "error",
            "message": e.message,
        })
        yield f"event: error\ndata: {error_event}\n\n"
    except Exception as e:
        logger.exception("Unexpected error in chat stream")
        error_event = json.dumps({
            "type": "error",
            "message": "An unexpected error occurred. Please try again.",
        })
        yield f"event: error\ndata: {error_event}\n\n"


@router.post("/chat", tags=["Chat"])
async def chat(request: ChatRequest, http_request: Request):
    """
    Process a user query through the RAG pipeline.

    Returns a streaming response using Server-Sent Events (SSE).

    Events:
    - `meta`: Contains conversation_id
    - `content`: Text chunks as they arrive
    - `sources`: List of source documents used
    - `done`: Stream complete
    - `error`: Error occurred
    """
    rag_engine = get_rag_engine()

    return StreamingResponse(
        _sse_stream(rag_engine, request, http_request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
