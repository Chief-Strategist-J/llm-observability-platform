"""Base HTTP client with single responsibility."""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import httpx
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from shared.errors.codes import http_request_failed

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


@dataclass
class ClientConfig:
    """Client configuration with single responsibility"""
    base_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = True


class BaseClient:
    """Base HTTP client with single responsibility"""
    
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
        """Make HTTP request with tracing"""
        with _tracer.start_as_current_span("http_request") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "http-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("http.method", method)
            span.set_attribute("http.endpoint", endpoint)
            span.set_attribute("http.base_url", self.base_url)
            
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.client.request(method, url, headers=self.headers, **kwargs)
                response.raise_for_status()
                
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.url", str(response.url))
                
                logger.info("event=http_request method=%s url=%s status=%d", method, url, response.status_code)
                return response.json()
                
            except httpx.HTTPStatusError as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("http.status_code", e.response.status_code if hasattr(e, 'response') else 0)
                span.set_attribute("http.error", str(e))
                logger.error("event=http_request_failed method=%s url=%s error=%s", method, endpoint, str(e))
                raise http_request_failed(f"HTTP request failed: {str(e)}")
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("http.error", str(e))
                logger.error("event=http_request_error method=%s url=%s error=%s", method, endpoint, str(e))
                raise http_request_failed(f"HTTP request error: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request"""
        return self._make_request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request"""
        return self._make_request("POST", endpoint, data=data, json=json)
    
    def put(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        """Make PUT request"""
        return self._make_request("PUT", endpoint, data=data, json=json)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request"""
        return self._make_request("DELETE", endpoint)
    
    def close(self):
        """Close client"""
        with _tracer.start_as_current_span("close_client") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "http-client")
            span.set_attribute("api.version", "v1")
            
            try:
                self.client.close()
                span.set_attribute("close.result", "success")
                logger.info("event=http_client_closed")
            except Exception as e:
                span.record_error(e)
                span.set_attribute("close.result", "error")
                logger.error("event=http_client_close_error error=%s", str(e))
