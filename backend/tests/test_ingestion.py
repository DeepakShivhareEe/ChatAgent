"""
Tests for document ingestion loaders.
"""

import os
import json
import tempfile
import pytest
from app.ingestion.loaders.markdown import MarkdownLoader
from app.ingestion.loaders.html import HTMLLoader
from app.ingestion.loaders.json_loader import JSONLoader
from app.ingestion.loaders.text import TextLoader
from app.ingestion.pipeline import IngestionPipeline


class TestMarkdownLoader:
    """Test Markdown file loader."""

    def test_load_markdown(self, tmp_path):
        filepath = tmp_path / "test.md"
        filepath.write_text("# Hello\n\nThis is a test document.", encoding="utf-8")

        loader = MarkdownLoader()
        docs = loader.load(str(filepath))

        assert len(docs) == 1
        assert "Hello" in docs[0].content
        assert docs[0].metadata["source"] == "test.md"
        assert docs[0].metadata["title"] == "Hello"

    def test_load_empty_file(self, tmp_path):
        filepath = tmp_path / "empty.md"
        filepath.write_text("", encoding="utf-8")

        loader = MarkdownLoader()
        docs = loader.load(str(filepath))
        assert len(docs) == 0

    def test_can_load(self):
        loader = MarkdownLoader()
        assert loader.can_load("file.md") is True
        assert loader.can_load("file.markdown") is True
        assert loader.can_load("file.txt") is False


class TestHTMLLoader:
    """Test HTML file loader."""

    def test_load_html(self, tmp_path):
        filepath = tmp_path / "test.html"
        filepath.write_text(
            "<html><head><title>Test Page</title></head>"
            "<body><h1>Welcome</h1><p>Content here.</p>"
            "<script>alert('xss')</script></body></html>",
            encoding="utf-8",
        )

        loader = HTMLLoader()
        docs = loader.load(str(filepath))

        assert len(docs) == 1
        assert "Welcome" in docs[0].content
        assert "Content here" in docs[0].content
        assert "alert" not in docs[0].content  # Script removed
        assert docs[0].metadata["title"] == "Test Page"

    def test_load_html_strips_nav(self, tmp_path):
        filepath = tmp_path / "nav.html"
        filepath.write_text(
            "<html><body><nav>Navigation</nav><main>Main content</main></body></html>",
            encoding="utf-8",
        )

        loader = HTMLLoader()
        docs = loader.load(str(filepath))
        assert "Navigation" not in docs[0].content
        assert "Main content" in docs[0].content


class TestJSONLoader:
    """Test JSON file loader."""

    def test_load_flat_json(self, tmp_path):
        filepath = tmp_path / "test.json"
        data = {"name": "Test", "description": "A test document", "version": 1}
        filepath.write_text(json.dumps(data), encoding="utf-8")

        loader = JSONLoader()
        docs = loader.load(str(filepath))

        assert len(docs) == 1
        assert "name: Test" in docs[0].content
        assert "description: A test document" in docs[0].content

    def test_load_nested_json(self, tmp_path):
        filepath = tmp_path / "nested.json"
        data = {"company": {"name": "ACME", "employees": [{"name": "Alice"}]}}
        filepath.write_text(json.dumps(data), encoding="utf-8")

        loader = JSONLoader()
        docs = loader.load(str(filepath))
        assert "company.name: ACME" in docs[0].content
        assert "Alice" in docs[0].content


class TestTextLoader:
    """Test plain text file loader."""

    def test_load_text(self, tmp_path):
        filepath = tmp_path / "test.txt"
        filepath.write_text("Hello, this is plain text.", encoding="utf-8")

        loader = TextLoader()
        docs = loader.load(str(filepath))

        assert len(docs) == 1
        assert docs[0].content == "Hello, this is plain text."
        assert docs[0].metadata["source"] == "test.txt"

    def test_load_empty_text(self, tmp_path):
        filepath = tmp_path / "empty.txt"
        filepath.write_text("   ", encoding="utf-8")

        loader = TextLoader()
        docs = loader.load(str(filepath))
        assert len(docs) == 0


class TestIngestionLimits:
    def test_scan_directory_respects_file_limit(self, tmp_path):
        for index in range(3):
            (tmp_path / f"document-{index}.txt").write_text("content", encoding="utf-8")

        pipeline = IngestionPipeline(db_client=None, max_files=2)  # type: ignore[arg-type]
        assert len(pipeline._scan_directory(str(tmp_path))) == 2
