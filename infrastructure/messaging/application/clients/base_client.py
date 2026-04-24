import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ClientConfig:
    base_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = True


class BaseClient:
    def __init__(self, config: ClientConfig):
        self.config = config
        self.base_url = config.base_url.rstrip('/')
        self.client = httpx.Client(
            timeout=config.timeout,
            verify=config.verify_ssl
        )
        self.headers = {}
        if config.api_key:
            self.headers["Authorization"] = f"Bearer {config.api_key}"
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        response = self.client.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        return self._make_request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        return self._make_request("POST", endpoint, json=data)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        return self._make_request("PUT", endpoint, json=data)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        return self._make_request("DELETE", endpoint)
    
    def close(self):
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
