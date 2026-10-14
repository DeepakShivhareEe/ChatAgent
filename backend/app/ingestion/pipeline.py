"""
Document ingestion pipeline — scans directories, loads documents,
chunks text, generates embeddings, and stores in vector DB.
"""

import os
import logging
from typing import Optional

from app.ingestion.loaders.base import BaseLoader, Document
from app.ingestion.loaders.markdown import MarkdownLoader
from app.ingestion.loaders.html import HTMLLoader
from app.ingestion.loaders.pdf import PDFLoader
from app.ingestion.loaders.docx import DOCXLoader
from app.ingestion.loaders.json_loader import JSONLoader
from app.ingestion.loaders.text import TextLoader
from app.rag.chunker import TextChunker
from app.vectordb.chromadb import ChromaDBClient

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Orchestrates document ingestion from directory to vector DB."""

    def __init__(
        self,
        db_client: ChromaDBClient,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        max_file_bytes: int = 10_000_000,
        max_files: int = 1000,
    ):
        self.db_client = db_client
        self.chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self.max_file_bytes = max_file_bytes
        self.max_files = max_files

        # Register all loaders
        self.loaders: list[BaseLoader] = [
            MarkdownLoader(),
            HTMLLoader(),
            PDFLoader(),
            DOCXLoader(),
            JSONLoader(),
            TextLoader(),
        ]

    def _get_loader(self, filepath: str) -> Optional[BaseLoader]:
        """Find the appropriate loader for a file."""
        for loader in self.loaders:
            if loader.can_load(filepath):
                return loader
        return None

    def _scan_directory(self, directory: str) -> list[str]:
        """Recursively scan a directory for supported files."""
        supported_extensions = set()
        for loader in self.loaders:
            supported_extensions.update(loader.SUPPORTED_EXTENSIONS)

        files = []
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                ext = os.path.splitext(filename)[1].lower()
                if ext in supported_extensions:
                    files.append(filepath)

        return sorted(files)[:self.max_files]

    async def ingest(
        self,
        directory: str,
        clear_existing: bool = False,
    ) -> dict:
        """
        Run the full ingestion pipeline.

        Args:
            directory: Path to the knowledge directory.
            clear_existing: If True, clear existing vectors first.

        Returns:
            Stats dict with documents_processed, chunks_created, errors.
        """
        stats = {
            "documents_processed": 0,
            "chunks_created": 0,
            "errors": [],
        }

        # Validate directory
        if not os.path.isdir(directory):
            stats["errors"].append(f"Directory not found: {directory}")
            return stats

        # Clear existing data if requested
        if clear_existing:
            await self.db_client.clear_collection()
            logger.info("Cleared existing vector collection")

        # Scan for files
        files = self._scan_directory(directory)
        logger.info(f"Found {len(files)} supported files in {directory}")

        if not files:
            stats["errors"].append(f"No supported files found in {directory}")
            return stats

        # Process each file
        all_chunks = []
        for filepath in files:
            try:
                if os.path.getsize(filepath) > self.max_file_bytes:
                    stats["errors"].append(
                        f"Skipped {os.path.basename(filepath)}: file exceeds size limit."
                    )
                    continue
                loader = self._get_loader(filepath)
                if loader is None:
                    continue

                # Load document
                documents = loader.load(filepath)
                stats["documents_processed"] += 1

                # Chunk each document
                for doc in documents:
                    if doc.is_empty:
                        continue
                    chunks = self.chunker.chunk_text(
                        text=doc.content,
                        metadata=doc.metadata,
                    )
                    all_chunks.extend(chunks)

                logger.info(f"Processed: {os.path.basename(filepath)}")

            except Exception as e:
                error_msg = f"Error processing {os.path.basename(filepath)}: {e}"
                logger.warning(error_msg)
                stats["errors"].append(error_msg)

        # Store chunks in vector DB
        if all_chunks:
            await self.db_client.add_documents(all_chunks)
            stats["chunks_created"] = len(all_chunks)
            logger.info(f"Stored {len(all_chunks)} chunks in vector DB")

        return stats
