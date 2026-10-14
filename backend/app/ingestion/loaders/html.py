"""
HTML document loader — extracts text from HTML files.
"""

from bs4 import BeautifulSoup
from app.ingestion.loaders.base import BaseLoader, Document
from app.models.exceptions import DocumentLoadError


class HTMLLoader(BaseLoader):
    """Load HTML (.html, .htm) files and extract text content."""

    SUPPORTED_EXTENSIONS = [".html", ".htm"]

    # Tags to remove entirely (scripts, styles, etc.)
    REMOVE_TAGS = ["script", "style", "nav", "footer", "header", "noscript", "svg"]

    def load(self, filepath: str) -> list[Document]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, "html.parser")

            # Remove unwanted tags
            for tag in self.REMOVE_TAGS:
                for element in soup.find_all(tag):
                    element.decompose()

            # Extract text
            text = soup.get_text(separator="\n", strip=True)

            if not text.strip():
                return []

            metadata = self._base_metadata(filepath)

            # Extract title
            title_tag = soup.find("title")
            if title_tag and title_tag.string:
                metadata["title"] = title_tag.string.strip()

            # Extract meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                metadata["description"] = meta_desc["content"]

            return [Document(content=text, metadata=metadata)]
        except Exception as e:
            raise DocumentLoadError(filepath, str(e))
