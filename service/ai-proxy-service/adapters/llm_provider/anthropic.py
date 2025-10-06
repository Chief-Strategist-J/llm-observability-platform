from core.domain.models import LLMResponse
from core.ports.llm_provider import LLMProviderPort
import httpx


class AnthropicLLM(LLMProviderPort):
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
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["content"][0]["text"], provider="anthropic", model=self.model
            )
