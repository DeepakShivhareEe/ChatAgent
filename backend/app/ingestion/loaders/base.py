"""
Abstract base class for document loaders.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Document:
    """A loaded document with content and metadata."""
    content: str
    metadata: dict = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.content or not self.content.strip()


class BaseLoader(ABC):
    """Abstract document loader interface."""

    # File extensions this loader handles
    SUPPORTED_EXTENSIONS: list[str] = []

    @abstractmethod
    def load(self, filepath: str) -> list[Document]:
        """
        Load a file and return a list of Document objects.

        Args:
            filepath: Absolute path to the file.

        Returns:
            List of Document objects with content and metadata.
        """
        pass

    def can_load(self, filepath: str) -> bool:
        """Check if this loader supports the given file."""
        return any(filepath.lower().endswith(ext) for ext in self.SUPPORTED_EXTENSIONS)

    def _base_metadata(self, filepath: str) -> dict:
        """Generate base metadata for a document."""
        import os
        return {
            "source": os.path.basename(filepath),
            "filepath": filepath,
            "file_type": os.path.splitext(filepath)[1].lower(),
        }
