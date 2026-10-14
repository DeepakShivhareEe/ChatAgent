"""
Vector search retriever — queries ChromaDB for relevant document chunks.
"""

from app.vectordb.chromadb import ChromaDBClient


class Retriever:
    """Retrieves relevant document chunks from the vector database."""

    def __init__(self, db_client: ChromaDBClient, top_k: int = 5,
                 similarity_threshold: float = 0.3):
        self.db_client = db_client
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    async def retrieve(
        self, query: str, top_k: int | None = None
    ) -> list[dict]:
        """
        Retrieve the most relevant chunks for a query.

        Args:
            query: User's question.
            top_k: Override default top_k.

        Returns:
            List of dicts with 'content', 'metadata', and 'score'.
        """
        k = top_k or self.top_k
        results = await self.db_client.query(
            query_text=query,
            n_results=k,
        )

        # Filter by similarity threshold and format results
        filtered = []
        for result in results:
            # ChromaDB returns distances; lower = more similar
            # Convert distance to similarity score (1 - distance for cosine)
            score = 1.0 - result.get("distance", 1.0)
            if score >= self.similarity_threshold:
                filtered.append({
                    "content": result["content"],
                    "metadata": result.get("metadata", {}),
                    "score": round(score, 4),
                })

        # Sort by score descending
        filtered.sort(key=lambda x: x["score"], reverse=True)
        return filtered

    async def has_relevant_context(self, query: str) -> bool:
        """Check if any relevant context exists for a query."""
        results = await self.retrieve(query, top_k=1)
        return len(results) > 0
