"""
JSON document loader — extracts text from JSON files.
Handles both flat and nested JSON structures.
"""

import json
from app.ingestion.loaders.base import BaseLoader, Document
from app.models.exceptions import DocumentLoadError


class JSONLoader(BaseLoader):
    """Load JSON (.json) files and extract text content."""

    SUPPORTED_EXTENSIONS = [".json"]

    def load(self, filepath: str) -> list[Document]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            content = self._extract_text(data)

            if not content.strip():
                return []

            metadata = self._base_metadata(filepath)
            return [Document(content=content, metadata=metadata)]
        except Exception as e:
            raise DocumentLoadError(filepath, str(e))

    def _extract_text(self, data, prefix: str = "") -> str:
        """Recursively extract text from JSON data."""
        parts = []

        if isinstance(data, dict):
            for key, value in data.items():
                current_prefix = f"{prefix}.{key}" if prefix else key
                if isinstance(value, str):
                    parts.append(f"{current_prefix}: {value}")
                elif isinstance(value, (int, float, bool)):
                    parts.append(f"{current_prefix}: {value}")
                elif isinstance(value, (dict, list)):
                    nested = self._extract_text(value, current_prefix)
                    if nested:
                        parts.append(nested)

        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_prefix = f"{prefix}[{i}]"
                if isinstance(item, str):
                    parts.append(f"{current_prefix}: {item}")
                elif isinstance(item, (dict, list)):
                    nested = self._extract_text(item, current_prefix)
                    if nested:
                        parts.append(nested)

        return "\n".join(parts)
