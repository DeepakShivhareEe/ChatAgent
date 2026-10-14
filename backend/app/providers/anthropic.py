"""
Anthropic Claude LLM provider implementation.
"""

from typing import AsyncGenerator
from anthropic import AsyncAnthropic
from app.providers.base import LLMProvider
from app.models.exceptions import ProviderError


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str, model: str, temperature: float,
                 max_tokens: int, top_p: float):
        super().__init__(api_key, model, temperature, max_tokens, top_p)
        self.client = AsyncAnthropic(api_key=api_key)

    def _prepare_messages(self, messages: list[dict]) -> tuple[str, list[dict]]:
        """
        Separate system message from conversation messages.
        Anthropic requires system prompt as a separate parameter.
        """
        system_prompt = ""
        conversation = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt += msg["content"] + "\n"
            else:
                conversation.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })
        return system_prompt.strip(), conversation

    async def generate(self, messages: list[dict], stream: bool = False) -> str:
        self._validate_messages(messages)
        try:
            if stream:
                chunks = []
                async for chunk in self.generate_stream(messages):
                    chunks.append(chunk)
                return "".join(chunks)

            system_prompt, conversation = self._prepare_messages(messages)
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                system=system_prompt if system_prompt else "You are a helpful assistant.",
                messages=conversation,
            )
            return response.content[0].text
        except Exception as e:
            raise ProviderError(str(e), provider="anthropic")

    async def generate_stream(
        self, messages: list[dict]
    ) -> AsyncGenerator[str, None]:
        self._validate_messages(messages)
        try:
            system_prompt, conversation = self._prepare_messages(messages)
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                system=system_prompt if system_prompt else "You are a helpful assistant.",
                messages=conversation,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise ProviderError(str(e), provider="anthropic")
