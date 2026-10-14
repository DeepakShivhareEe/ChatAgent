"""
Tests for RAG pipeline components — chunker and prompt builder.
"""

import pytest
from app.rag.chunker import TextChunker
from app.rag.prompt import PromptBuilder, FALLBACK_RESPONSE


class TestTextChunker:
    """Test document chunking."""

    def test_empty_text_returns_empty(self):
        chunker = TextChunker(chunk_size=100)
        assert chunker.chunk_text("") == []
        assert chunker.chunk_text("   ") == []

    def test_short_text_single_chunk(self):
        chunker = TextChunker(chunk_size=500)
        chunks = chunker.chunk_text("Hello, world!")
        assert len(chunks) == 1
        assert chunks[0]["content"] == "Hello, world!"

    def test_chunk_metadata_preserved(self):
        chunker = TextChunker(chunk_size=500)
        meta = {"source": "test.md", "title": "Test"}
        chunks = chunker.chunk_text("Hello", metadata=meta)
        assert chunks[0]["metadata"]["source"] == "test.md"
        assert chunks[0]["metadata"]["title"] == "Test"
        assert chunks[0]["metadata"]["chunk_index"] == 0

    def test_long_text_creates_multiple_chunks(self):
        chunker = TextChunker(chunk_size=50, chunk_overlap=0)
        text = "This is a test. " * 20  # ~320 chars
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 1

    def test_chunk_size_respected(self):
        chunker = TextChunker(chunk_size=100, chunk_overlap=0)
        text = "Word " * 100  # 500 chars
        chunks = chunker.chunk_text(text)
        for chunk in chunks:
            # Allow small overshoot due to overlap
            assert len(chunk["content"]) <= 150

    def test_chunk_indices_sequential(self):
        chunker = TextChunker(chunk_size=50, chunk_overlap=0)
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        chunks = chunker.chunk_text(text)
        for i, chunk in enumerate(chunks):
            assert chunk["metadata"]["chunk_index"] == i


class TestPromptBuilder:
    """Test prompt construction."""

    def test_build_messages_structure(self):
        builder = PromptBuilder(website_name="TestSite", assistant_name="TestBot")
        chunks = [
            {"content": "Feature A does X.", "metadata": {"source": "docs.md"}}
        ]
        messages = builder.build_messages("What does Feature A do?", chunks)

        assert len(messages) == 2  # system + user
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Feature A does X." in messages[0]["content"]
        assert "TestSite" in messages[0]["content"]

    def test_build_messages_with_history(self):
        builder = PromptBuilder()
        chunks = [{"content": "Context", "metadata": {"source": "faq.md"}}]
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        messages = builder.build_messages("Follow up?", chunks, history)

        assert len(messages) == 4  # system + 2 history + user
        assert messages[1]["content"] == "Hi"
        assert messages[2]["content"] == "Hello!"
        assert messages[3]["content"] == "Follow up?"

    def test_empty_context_shows_no_context(self):
        builder = PromptBuilder()
        messages = builder.build_messages("Test?", [])
        assert "No relevant context found" in messages[0]["content"]

    def test_fallback_response(self):
        builder = PromptBuilder()
        assert "knowledge base" in builder.fallback_response.lower()
        assert builder.fallback_response == FALLBACK_RESPONSE

    def test_source_formatting(self):
        builder = PromptBuilder()
        chunks = [
            {"content": "Content A", "metadata": {"source": "page1.md"}},
            {"content": "Content B", "metadata": {"source": "page2.md"}},
        ]
        messages = builder.build_messages("Query", chunks)
        system = messages[0]["content"]
        assert "Source 1: page1.md" in system
        assert "Source 2: page2.md" in system
