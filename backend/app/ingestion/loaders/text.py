"""
Plain text document loader.
"""

from app.ingestion.loaders.base import BaseLoader, Document
from app.models.exceptions import DocumentLoadError


class TextLoader(BaseLoader):
    """Load plain text (.txt) files."""

    SUPPORTED_EXTENSIONS = [".txt"]

    def load(self, filepath: str) -> list[Document]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                return []

            metadata = self._base_metadata(filepath)
            return [Document(content=content, metadata=metadata)]
        except Exception as e:
            raise DocumentLoadError(filepath, str(e))
