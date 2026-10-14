"""
Abstract base class for all LLM providers.
Every provider must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    def __init__(self, api_key: str, model: str, temperature: float,
                 max_tokens: int, top_p: float):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p

    @property
    def provider_name(self) -> str:
        """Return the provider name for logging and status."""
        return self.__class__.__name__.replace("Provider", "").lower()

    @abstractmethod
    async def generate(self, messages: list[dict], stream: bool = False) -> str:
        """
        Generate a response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            stream: If True, use generate_stream instead.

        Returns:
            The full generated text response.
        """
        pass

    @abstractmethod
    async def generate_stream(
        self, messages: list[dict]
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.

        Yields:
            Text chunks as they arrive from the provider.
        """
        pass

    def _validate_messages(self, messages: list[dict]) -> None:
        """Validate message format before sending to provider."""
        if not messages:
            raise ValueError("Messages list cannot be empty.")
        for msg in messages:
            if "role" not in msg or "content" not in msg:
                raise ValueError(
                    f"Each message must have 'role' and 'content'. Got: {msg}"
                )
