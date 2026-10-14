"""
ChromaDB client wrapper — manages the persistent vector database.
"""

import hashlib
import logging
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.ingestion.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """Persistent ChromaDB client with embedding support."""

    def __init__(
        self,
        persist_directory: str = "./data/chromadb",
        collection_name: str = "website_knowledge",
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_service = embedding_service

        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            f"ChromaDB initialized at {persist_directory}, "
            f"collection '{collection_name}' has {self.collection.count()} documents"
        )

    def _generate_id(self, content: str, metadata: dict) -> str:
        """Generate a deterministic ID for a document chunk."""
        source = metadata.get("source", "unknown")
        chunk_index = metadata.get("chunk_index", 0)
        hash_input = f"{source}:{chunk_index}:{content[:100]}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    async def add_documents(self, chunks: list[dict]) -> int:
        """
        Add document chunks to the collection.

        Args:
            chunks: List of dicts with 'content' and 'metadata'.

        Returns:
            Number of chunks added.
        """
        if not chunks:
            return 0

        contents = [chunk["content"] for chunk in chunks]
        metadatas = []
        ids = []

        for chunk in chunks:
            # Flatten metadata values to strings for ChromaDB compatibility
            meta = {}
            for k, v in chunk.get("metadata", {}).items():
                if isinstance(v, (str, int, float, bool)):
                    meta[k] = v
                else:
                    meta[k] = str(v)
            metadatas.append(meta)
            ids.append(self._generate_id(chunk["content"], chunk.get("metadata", {})))

        # Generate embeddings
        if self.embedding_service:
            embeddings = self.embedding_service.embed_texts(contents)
            self.collection.upsert(
                ids=ids,
                documents=contents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
        else:
            # Let ChromaDB handle embedding (uses default model)
            self.collection.upsert(
                ids=ids,
                documents=contents,
                metadatas=metadatas,
            )

        logger.info(f"Upserted {len(chunks)} chunks into collection")
        return len(chunks)

    async def query(
        self,
        query_text: str,
        n_results: int = 5,
    ) -> list[dict]:
        """
        Query the collection for relevant documents.

        Args:
            query_text: The search query.
            n_results: Number of results to return.

        Returns:
            List of dicts with 'content', 'metadata', 'distance'.
        """
        if self.collection.count() == 0:
            return []

        # Generate query embedding
        if self.embedding_service:
            query_embedding = self.embedding_service.embed_query(query_text)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, self.collection.count()),
            )
        else:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(n_results, self.collection.count()),
            )

        # Format results
        formatted = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                formatted.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 1.0,
                })

        return formatted

    async def clear_collection(self) -> None:
        """Delete and recreate the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Collection '{self.collection_name}' cleared")

    def get_stats(self) -> dict:
        """Return collection statistics."""
        return {
            "collection_name": self.collection_name,
            "document_count": self.collection.count(),
            "persist_directory": self.persist_directory,
        }
