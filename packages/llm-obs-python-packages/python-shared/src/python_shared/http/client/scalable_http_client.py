import httpx
from typing import Any, Dict, Optional
from python_shared.http.resilience.standard_circuit_breaker import StandardCircuitBreaker
from python_shared.http.resilience.retry_policy import RetryPolicy

class ResilientHttpClient:
    def __init__(self, base_url: str = "", timeout: float = 10.0, max_retries: int = 3):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.circuit_breaker = StandardCircuitBreaker()
        self.retry_policy = RetryPolicy(max_retries=max_retries)
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            transport=httpx.HTTPTransport(retries=max_retries)
        )
        self._async_client: Optional[httpx.AsyncClient] = None

    def get(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        key = self.circuit_breaker.get_circuit_key("default", url)
        if not self.circuit_breaker.can_execute(key):
            raise RuntimeError(f"Circuit breaker OPEN for {key}")
        try:
            res = self._client.get(url, params=params, headers=headers)
            self.circuit_breaker.on_success(key)
            return res
        except Exception as e:
            self.circuit_breaker.on_failure(key)
            raise e

    def post(self, url: str, json: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        key = self.circuit_breaker.get_circuit_key("default", url)
        if not self.circuit_breaker.can_execute(key):
            raise RuntimeError(f"Circuit breaker OPEN for {key}")
        try:
            res = self._client.post(url, json=json, headers=headers)
            self.circuit_breaker.on_success(key)
            return res
        except Exception as e:
            self.circuit_breaker.on_failure(key)
            raise e

    def put(self, url: str, json: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        key = self.circuit_breaker.get_circuit_key("default", url)
        if not self.circuit_breaker.can_execute(key):
            raise RuntimeError(f"Circuit breaker OPEN for {key}")
        try:
            res = self._client.put(url, json=json, headers=headers)
            self.circuit_breaker.on_success(key)
            return res
        except Exception as e:
            self.circuit_breaker.on_failure(key)
            raise e

    def patch(self, url: str, json: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        key = self.circuit_breaker.get_circuit_key("default", url)
        if not self.circuit_breaker.can_execute(key):
            raise RuntimeError(f"Circuit breaker OPEN for {key}")
        try:
            res = self._client.patch(url, json=json, headers=headers)
            self.circuit_breaker.on_success(key)
            return res
        except Exception as e:
            self.circuit_breaker.on_failure(key)
            raise e

    def delete(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        key = self.circuit_breaker.get_circuit_key("default", url)
        if not self.circuit_breaker.can_execute(key):
            raise RuntimeError(f"Circuit breaker OPEN for {key}")
        try:
            res = self._client.delete(url, params=params, headers=headers)
            self.circuit_breaker.on_success(key)
            return res
        except Exception as e:
            self.circuit_breaker.on_failure(key)
            raise e

    def close(self):
        self._client.close()
        if self._async_client:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._async_client.aclose())
            except RuntimeError:
                pass

httpClient = ResilientHttpClient()
