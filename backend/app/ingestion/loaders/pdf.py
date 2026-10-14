"""
PDF document loader — extracts text from PDF files.
"""

from PyPDF2 import PdfReader
from app.ingestion.loaders.base import BaseLoader, Document
from app.models.exceptions import DocumentLoadError


class PDFLoader(BaseLoader):
    """Load PDF (.pdf) files and extract text content."""

    SUPPORTED_EXTENSIONS = [".pdf"]

    def load(self, filepath: str) -> list[Document]:
        try:
            reader = PdfReader(filepath)
            pages = []

            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    metadata = self._base_metadata(filepath)
                    metadata["page_number"] = i + 1
                    metadata["total_pages"] = len(reader.pages)
                    pages.append(Document(content=text, metadata=metadata))

            # Extract document info if available
            if reader.metadata:
                for doc in pages:
                    if reader.metadata.title:
                        doc.metadata["title"] = reader.metadata.title
                    if reader.metadata.author:
                        doc.metadata["author"] = reader.metadata.author

            return pages
        except Exception as e:
            raise DocumentLoadError(filepath, str(e))
