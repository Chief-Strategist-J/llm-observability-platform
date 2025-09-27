import json
import httpx
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class CloudflareAIClient:
    """Async client for Cloudflare Workers AI API"""
    
    def __init__(self, account_id: str, api_token: str, timeout: float = 30):
        self.account_id = account_id
        self.api_token = api_token
        self.timeout = timeout
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run"
        
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "User-Agent": "CloudflareAI-Proxy/1.0"
        }
    
    async def generate_text(
        self,
        model_id: str,
        prompt: str,
        **inference_params: Any
    ) -> Dict[str, Any]:
        """Generate text using Cloudflare Workers AI"""
        url = f"{self.base_url}/{model_id}"
        
        payload = {
            "prompt": prompt,
            **inference_params
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Calling Cloudflare AI: {model_id}")
                response = await client.post(
                    url,
                    headers=self.headers,
                    content=json.dumps(payload)
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            logger.error(f"Timeout calling Cloudflare AI after {self.timeout}s")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

    async def health_check(self) -> bool:
        """Simple health check by making a minimal API call"""
        try:
            await self.generate_text(
                model_id="@cf/meta/llama-3.2-1b-instruct",
                prompt="Hi",
                max_tokens=1
            )
            return True
        except Exception:
            return False
