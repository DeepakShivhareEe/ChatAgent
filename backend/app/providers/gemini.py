"""
Google Gemini LLM provider implementation.
"""

from typing import AsyncGenerator
from google import genai
from google.genai import types
from app.providers.base import LLMProvider
from app.models.exceptions import ProviderError


class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""

    def __init__(self, api_key: str, model: str, temperature: float,
                 max_tokens: int, top_p: float):
        super().__init__(api_key, model, temperature, max_tokens, top_p)
        self.client = genai.Client(api_key=api_key)

    def _prepare_contents(self, messages: list[dict]) -> tuple[str | None, list[types.Content]]:
        """
        Convert messages to Gemini format.
        Extract system instruction and convert roles.
        """
        system_instruction = None
        contents = []

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg["content"])],
                    )
                )
        return system_instruction, contents

    def _get_config(self) -> types.GenerateContentConfig:
        """Build generation config."""
        return types.GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            top_p=self.top_p,
        )

    async def generate(self, messages: list[dict], stream: bool = False) -> str:
        self._validate_messages(messages)
        try:
            if stream:
                chunks = []
                async for chunk in self.generate_stream(messages):
                    chunks.append(chunk)
                return "".join(chunks)

            system_instruction, contents = self._prepare_contents(messages)
            config = self._get_config()
            if system_instruction:
                config.system_instruction = system_instruction

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            return response.text or ""
        except Exception as e:
            raise ProviderError(str(e), provider="gemini")

    async def generate_stream(
        self, messages: list[dict]
    ) -> AsyncGenerator[str, None]:
        self._validate_messages(messages)
        try:
            system_instruction, contents = self._prepare_contents(messages)
            config = self._get_config()
            if system_instruction:
                config.system_instruction = system_instruction

            async for chunk in self.client.aio.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=config,
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise ProviderError(str(e), provider="gemini")
