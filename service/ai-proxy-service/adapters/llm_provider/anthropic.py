"""Anthropic LLM provider adapter for the AI Proxy Service.

Implements the LLMProviderPort interface to interact with Anthropic's AI
message/completion API asynchronously.

"""

import logging

import httpx

from ...core.domain.models import LLMResponse
from ...core.ports.llm_provider import LLMProviderPort

logger = logging.getLogger(__name__)


class AnthropicLLM(LLMProviderPort):
    """Anthropic LLM provider implementation.

    Attributes:
        api_key (str): Anthropic API key for authentication.
        model (str): Model name to use for completions.
        url (str): Anthropic API endpoint for messages/completions.
        headers (dict): Authorization headers for API requests.

    """

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    async def generate(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> LLMResponse:
        """Generate text from a prompt using Anthropic's API.

        Args:
            prompt (str): Text prompt to send to the model.
            max_tokens (int): Maximum number of tokens to generate.
            temperature (float): Sampling temperature controlling randomness.

        Returns:
            LLMResponse: Object containing generated text, provider, and model.

        """
        logger.debug(
            "Generating text with Anthropic model=%s prompt_length=%d",
            self.model,
            len(prompt),
        )
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error("Anthropic API request failed: %s", e)
                raise
            data = response.json()
            return LLMResponse(
                text=data["content"][0]["text"],
                provider="anthropic",
                model=self.model,
            )
