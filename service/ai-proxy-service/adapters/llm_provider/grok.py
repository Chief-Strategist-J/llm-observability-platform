"""Grok LLM provider adapter for the AI Proxy Service.

Implements the LLMProviderPort interface to interact with Grok's chat/completion API
asynchronously.

"""

import logging

import httpx

from ...core.domain.models import LLMResponse
from ...core.ports.llm_provider import LLMProviderPort

logger = logging.getLogger(__name__)


class GrokLLM(LLMProviderPort):
    """Grok LLM provider implementation.

    Attributes:
        api_key (str): Grok API key for authentication.
        model (str): Model name to use for completions.
        url (str): Grok API endpoint for chat completions.
        headers (dict): Authorization headers for API requests.

    """

    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.url = f"{base_url}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def generate(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> LLMResponse:
        """Generate text from a prompt using Grok's API.

        Args:
            prompt (str): Text prompt to send to the model.
            max_tokens (int): Maximum number of tokens to generate.
            temperature (float): Sampling temperature controlling randomness.

        Returns:
            LLMResponse: Object containing generated text, provider, and model.

        """
        logger.debug(
            "Generating text with Grok model=%s prompt_length=%d",
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
                logger.error("Grok API request failed: %s", e)
                raise
            data = response.json()
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                provider="grok",
                model=self.model,
            )
