"""
OpenAI LLM provider implementation.
"""

from typing import AsyncGenerator
from openai import AsyncOpenAI
from app.providers.base import LLMProvider
from app.models.exceptions import ProviderError


class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT-4o, GPT-4o-mini, etc.)."""

    def __init__(self, api_key: str, model: str, temperature: float,
                 max_tokens: int, top_p: float):
        super().__init__(api_key, model, temperature, max_tokens, top_p)
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(self, messages: list[dict], stream: bool = False) -> str:
        self._validate_messages(messages)
        try:
            if stream:
                chunks = []
                async for chunk in self.generate_stream(messages):
                    chunks.append(chunk)
                return "".join(chunks)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise ProviderError(str(e), provider="openai")

    async def generate_stream(
        self, messages: list[dict]
    ) -> AsyncGenerator[str, None]:
        self._validate_messages(messages)
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
        except Exception as e:
            raise ProviderError(str(e), provider="openai")
