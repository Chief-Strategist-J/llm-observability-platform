import httpx
from typing import Any, Dict, Optional
from python_shared.http.resilience import CircuitBreaker

class ResilientHttpClient:
    """Scalable HTTP client facade with built-in retries and circuit breaker."""
    
    def __init__(self, base_url: str = "", timeout: float = 10.0, max_retries: int = 3):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.circuit_breaker = CircuitBreaker()
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            transport=httpx.HTTPTransport(retries=max_retries)
        )

    def get(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        return self.circuit_breaker.execute(self._client.get, url, params=params, headers=headers)

    def post(self, url: str, json: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        return self.circuit_breaker.execute(self._client.post, url, json=json, headers=headers)

    def close(self):
        self._client.close()
