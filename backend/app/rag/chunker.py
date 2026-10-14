"""
Document chunker — splits text into overlapping chunks for vector storage.
Uses recursive character splitting for natural breakpoints.
"""


class TextChunker:
    """Split text into overlapping chunks at natural boundaries."""

    # Separators in priority order: paragraphs → sentences → words → characters
    SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, metadata: dict | None = None) -> list[dict]:
        """
        Split text into overlapping chunks.

        Args:
            text: The full text to chunk.
            metadata: Optional metadata to attach to each chunk.

        Returns:
            List of dicts with 'content' and 'metadata' keys.
        """
        if not text or not text.strip():
            return []

        chunks = self._recursive_split(text.strip(), self.SEPARATORS)
        result = []
        for i, chunk in enumerate(chunks):
            chunk_meta = {**(metadata or {}), "chunk_index": i}
            result.append({
                "content": chunk.strip(),
                "metadata": chunk_meta,
            })
        return result

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using separators in priority order."""
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        # Try each separator
        for sep in separators:
            if sep == "":
                # Last resort: hard split by character count
                return self._hard_split(text)

            if sep not in text:
                continue

            parts = text.split(sep)
            chunks = []
            current_chunk = ""

            for part in parts:
                candidate = current_chunk + sep + part if current_chunk else part

                if len(candidate) <= self.chunk_size:
                    current_chunk = candidate
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    # If a single part exceeds chunk_size, split it further
                    if len(part) > self.chunk_size:
                        remaining_seps = separators[separators.index(sep) + 1:]
                        sub_chunks = self._recursive_split(part, remaining_seps)
                        chunks.extend(sub_chunks)
                        current_chunk = ""
                    else:
                        current_chunk = part

            if current_chunk:
                chunks.append(current_chunk)

            if len(chunks) > 1:
                # Apply overlap
                return self._apply_overlap(chunks)

        return [text]

    def _hard_split(self, text: str) -> list[str]:
        """Split text by character count as last resort."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start = end - self.chunk_overlap
        return chunks

    def _apply_overlap(self, chunks: list[str]) -> list[str]:
        """Add overlap between consecutive chunks."""
        if self.chunk_overlap <= 0 or len(chunks) <= 1:
            return chunks

        result = [chunks[0]]
        for i in range(1, len(chunks)):
            prev = chunks[i - 1]
            overlap_text = prev[-self.chunk_overlap:] if len(prev) > self.chunk_overlap else prev
            overlapped = overlap_text + chunks[i]
            # Trim if overlapped chunk exceeds limit
            if len(overlapped) > self.chunk_size:
                overlapped = overlapped[:self.chunk_size]
            result.append(overlapped)
        return result
