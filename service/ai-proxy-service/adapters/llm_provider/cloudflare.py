"""Cloudflare LLM provider adapter for the AI Proxy Service.

Implements the LLMProviderPort interface to interact with Cloudflare's AI completion API
asynchronously.

"""

import logging

import httpx

from ...core.domain.models import LLMResponse
from ...core.ports.llm_provider import LLMProviderPort

logger = logging.getLogger(__name__)


class CloudflareLLM(LLMProviderPort):
    """Cloudflare LLM provider implementation.

    Attributes:
        account_id (str): Cloudflare account ID for authentication.
        api_token (str): Cloudflare API token.
        model (str): Model name to use for completions.
        url (str): Cloudflare API endpoint for AI completions.
        headers (dict): Authorization headers for API requests.

    """

    def __init__(self, account_id: str, api_token: str, model: str):
        self.account_id = account_id
        self.api_token = api_token
        self.model = model
        self.url = (
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
        )
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

    async def generate(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> LLMResponse:
        """Generate text from a prompt using Cloudflare's AI API.

        Args:
            prompt (str): Text prompt to send to the model.
            max_tokens (int): Maximum number of tokens to generate.
            temperature (float): Sampling temperature controlling randomness.

        Returns:
            LLMResponse: Object containing generated text, provider, and model.

        """
        logger.debug(
            "Generating text with Cloudflare model=%s prompt_length=%d",
            self.model,
            len(prompt),
        )
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.url,
                headers=self.headers,
                json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error("Cloudflare API request failed: %s", e)
                raise
            data = response.json()
            return LLMResponse(
                text=data["result"]["response"],
                provider="cloudflare",
                model=self.model,
            )
