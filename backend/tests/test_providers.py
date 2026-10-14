"""
Tests for LLM provider factory and registry.
"""

import pytest
from app.providers.factory import get_provider, list_providers, PROVIDER_REGISTRY
from app.providers.base import LLMProvider
from app.providers.openai import OpenAIProvider
from app.providers.anthropic import AnthropicProvider
from app.providers.gemini import GeminiProvider
from app.providers.groq import GroqProvider
from app.providers.openrouter import OpenRouterProvider
from app.models.exceptions import ProviderNotFoundError


class TestProviderFactory:
    """Test provider factory resolution."""

    def test_list_providers(self):
        providers = list_providers()
        assert "openai" in providers
        assert "anthropic" in providers
        assert "gemini" in providers
        assert "groq" in providers
        assert "openrouter" in providers

    def test_registry_has_all_providers(self):
        assert len(PROVIDER_REGISTRY) == 5

    def test_get_openai_provider(self):
        provider = get_provider("openai", "test-key", "gpt-4o-mini")
        assert isinstance(provider, OpenAIProvider)
        assert isinstance(provider, LLMProvider)

    def test_get_anthropic_provider(self):
        provider = get_provider("anthropic", "test-key", "claude-3-haiku")
        assert isinstance(provider, AnthropicProvider)

    def test_get_gemini_provider(self):
        provider = get_provider("gemini", "test-key", "gemini-2.0-flash")
        assert isinstance(provider, GeminiProvider)

    def test_get_groq_provider(self):
        provider = get_provider("groq", "test-key", "llama-3.1-70b")
        assert isinstance(provider, GroqProvider)

    def test_get_openrouter_provider(self):
        provider = get_provider("openrouter", "test-key", "openai/gpt-4o")
        assert isinstance(provider, OpenRouterProvider)

    def test_provider_name_case_insensitive(self):
        provider = get_provider("OpenAI", "test-key", "gpt-4o")
        assert isinstance(provider, OpenAIProvider)

    def test_provider_name_with_whitespace(self):
        provider = get_provider("  openai  ", "test-key", "gpt-4o")
        assert isinstance(provider, OpenAIProvider)

    def test_invalid_provider_raises_error(self):
        with pytest.raises(ProviderNotFoundError):
            get_provider("nonexistent", "test-key", "model")

    def test_provider_stores_config(self):
        provider = get_provider(
            "openai", "test-key", "gpt-4o",
            temperature=0.5, max_tokens=2048, top_p=0.8,
        )
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4o"
        assert provider.temperature == 0.5
        assert provider.max_tokens == 2048
        assert provider.top_p == 0.8


class TestProviderBase:
    """Test base provider validation."""

    def test_validate_messages_empty_raises(self):
        provider = get_provider("openai", "test-key", "gpt-4o")
        with pytest.raises(ValueError, match="cannot be empty"):
            provider._validate_messages([])

    def test_validate_messages_missing_role_raises(self):
        provider = get_provider("openai", "test-key", "gpt-4o")
        with pytest.raises(ValueError, match="role"):
            provider._validate_messages([{"content": "hello"}])

    def test_validate_messages_valid(self):
        provider = get_provider("openai", "test-key", "gpt-4o")
        # Should not raise
        provider._validate_messages([
            {"role": "user", "content": "hello"}
        ])
