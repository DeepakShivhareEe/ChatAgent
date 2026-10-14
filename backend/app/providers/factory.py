"""
Provider factory — resolves the correct LLM provider from configuration.
"""

from app.providers.base import LLMProvider
from app.providers.openai import OpenAIProvider
from app.providers.anthropic import AnthropicProvider
from app.providers.gemini import GeminiProvider
from app.providers.groq import GroqProvider
from app.providers.openrouter import OpenRouterProvider
from app.models.exceptions import ProviderNotFoundError

# Registry of supported providers
PROVIDER_REGISTRY: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "openrouter": OpenRouterProvider,
}


def get_provider(
    provider_name: str,
    api_key: str,
    model: str,
    temperature: float = 0.3,
    max_tokens: int = 1024,
    top_p: float = 0.9,
) -> LLMProvider:
    """
    Create and return an LLM provider instance.

    Args:
        provider_name: One of 'openai', 'anthropic', 'gemini', 'groq', 'openrouter'.
        api_key: API key for the provider.
        model: Model name.
        temperature: Sampling temperature.
        max_tokens: Max response tokens.
        top_p: Top-p sampling.

    Returns:
        An instance of the requested LLMProvider.

    Raises:
        ProviderNotFoundError: If the provider is not supported.
    """
    provider_name = provider_name.lower().strip()
    provider_class = PROVIDER_REGISTRY.get(provider_name)

    if provider_class is None:
        raise ProviderNotFoundError(provider_name)

    return provider_class(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
    )


def list_providers() -> list[str]:
    """Return list of supported provider names."""
    return list(PROVIDER_REGISTRY.keys())
