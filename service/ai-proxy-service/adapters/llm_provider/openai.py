import httpx
from core.ports.llm_provider import LLMProviderPort
from core.domain.models import LLMResponse

class OpenAILLM(LLMProviderPort):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate(self, prompt: str, max_tokens: int, temperature: float) -> LLMResponse:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                provider="openai",
                model=self.model
            )
