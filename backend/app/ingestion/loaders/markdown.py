"""
Markdown document loader.
"""

from app.ingestion.loaders.base import BaseLoader, Document
from app.models.exceptions import DocumentLoadError


class MarkdownLoader(BaseLoader):
    """Load Markdown (.md) files."""

    SUPPORTED_EXTENSIONS = [".md", ".markdown"]

    def load(self, filepath: str) -> list[Document]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                return []

            metadata = self._base_metadata(filepath)
            # Extract title from first heading if present
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("# "):
                    metadata["title"] = line.lstrip("# ").strip()
                    break

            return [Document(content=content, metadata=metadata)]
        except Exception as e:
            raise DocumentLoadError(filepath, str(e))
