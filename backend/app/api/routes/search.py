"""
Search endpoint — direct vector search without LLM generation.
"""

from fastapi import APIRouter, Depends

from app.models.schemas import SearchRequest, SearchResponse, SearchResult
from app.api.dependencies import get_db_client
from app.security.admin import verify_admin_key

router = APIRouter()


@router.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_knowledge(request: SearchRequest, _: None = Depends(verify_admin_key)):
    """
    Search the knowledge base directly.

    Returns the most relevant document chunks with similarity scores.
    Useful for debugging and verifying knowledge base content.
    """
    db_client = get_db_client()

    results = await db_client.query(
        query_text=request.query,
        n_results=request.top_k or 5,
    )

    formatted_results = []
    for result in results:
        score = 1.0 - result.get("distance", 1.0)
        formatted_results.append(
            SearchResult(
                content=result["content"],
                source=result.get("metadata", {}).get("source", "Unknown"),
                score=round(score, 4),
                metadata=result.get("metadata", {}),
            )
        )

    return SearchResponse(
        results=formatted_results,
        query=request.query,
        total=len(formatted_results),
    )
