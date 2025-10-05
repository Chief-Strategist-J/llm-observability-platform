import httpx
from core.ports.llm_provider import LLMProviderPort
from core.domain.models import LLMResponse

class CloudflareLLM(LLMProviderPort):
    def __init__(self, account_id: str, api_token: str, model: str):
        self.account_id = account_id
        self.api_token = api_token
        self.model = model
        self.url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    async def generate(self, prompt: str, max_tokens: int, temperature: float) -> LLMResponse:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.url,
                headers=self.headers,
                json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["result"]["response"],
                provider="cloudflare",
                model=self.model
            )
