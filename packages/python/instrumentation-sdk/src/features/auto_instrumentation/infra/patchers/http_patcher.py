import importlib.util
import functools
import json
import re
from typing import Any, Dict, Optional, List
from ...ports import PatcherPort
from .base import execute_external_call_async, execute_external_call_sync
from ....manual_instrumentation.service import llm_span

# Common LLM provider patterns
LLM_ENDPOINT_PATTERNS = {
    "openai": [re.compile(r"api\.openai\.com/v1/chat/completions")],
    "anthropic": [re.compile(r"api\.anthropic\.com/v1/messages")],
    "google": [re.compile(r"generativelanguage\.googleapis\.com")],
    "cohere": [re.compile(r"api\.cohere\.ai/v1/chat")],
    "mistral": [re.compile(r"api\.mistral\.ai/v1/chat/completions")],
}

class HTTPPatcher(PatcherPort):
    def __init__(self):
        self._original_httpx_send = None
        self._original_httpx_async_send = None
        self._original_requests_send = None

    def is_installed(self) -> bool:
        return (importlib.util.find_spec("httpx") is not None or 
                importlib.util.find_spec("requests") is not None)

    def _detect_provider(self, url: str) -> Optional[str]:
        for provider, patterns in LLM_ENDPOINT_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(url):
                    return provider
        return None

    def _extract_model(self, body: Any) -> str:
        try:
            if isinstance(body, bytes):
                body = body.decode("utf-8")
            if isinstance(body, str):
                data = json.loads(body)
                return data.get("model", "unknown")
        except:
            pass
        return "unknown"

    def patch(self) -> None:
        # Patch httpx if installed
        if importlib.util.find_spec("httpx"):
            import httpx
            self._original_httpx_send = httpx.Client.send
            self._original_httpx_async_send = httpx.AsyncClient.send

            @functools.wraps(self._original_httpx_send)
            def patched_httpx_send(instance, request, **kwargs):
                provider = self._detect_provider(str(request.url))
                if provider:
                    model = self._extract_model(request.content)
                    with llm_span(model=model, provider=f"http:{provider}") as span:
                        return self._original_httpx_send(instance, request, **kwargs)
                return self._original_httpx_send(instance, request, **kwargs)

            @functools.wraps(self._original_httpx_async_send)
            async def patched_httpx_async_send(instance, request, **kwargs):
                provider = self._detect_provider(str(request.url))
                if provider:
                    model = self._extract_model(request.content)
                    async with llm_span(model=model, provider=f"http:{provider}") as span:
                        return await self._original_httpx_async_send(instance, request, **kwargs)
                return await self._original_httpx_async_send(instance, request, **kwargs)

            httpx.Client.send = patched_httpx_send
            httpx.AsyncClient.send = patched_httpx_async_send

        # Patch requests if installed
        if importlib.util.find_spec("requests"):
            import requests
            self._original_requests_send = requests.Session.send

            @functools.wraps(self._original_requests_send)
            def patched_requests_send(instance, request, **kwargs):
                provider = self._detect_provider(request.url)
                if provider:
                    model = self._extract_model(request.body)
                    with llm_span(model=model, provider=f"http:{provider}") as span:
                        return self._original_requests_send(instance, request, **kwargs)
                return self._original_requests_send(instance, request, **kwargs)

            requests.Session.send = patched_requests_send

    def patch_instance(self, instance: Any) -> None:
        """Manual patching for specific client instances."""
        import types
        import inspect
        
        # Check if it's an httpx client
        if hasattr(instance, "send") and hasattr(instance, "request"):
            original_send = instance.send
            if inspect.iscoroutinefunction(original_send):
                @functools.wraps(original_send)
                async def patched_send(request, **kwargs):
                    provider = self._detect_provider(str(request.url))
                    model = self._extract_model(request.content)
                    async with llm_span(model=model, provider=f"http:{provider}") as span:
                        return await original_send(request, **kwargs)
            else:
                @functools.wraps(original_send)
                def patched_send(request, **kwargs):
                    provider = self._detect_provider(str(request.url))
                    model = self._extract_model(request.content)
                    with llm_span(model=model, provider=f"http:{provider}") as span:
                        return original_send(request, **kwargs)
            instance.send = types.MethodType(patched_send, instance)

    def unpatch(self) -> None:
        if self._original_httpx_send:
            import httpx
            httpx.Client.send = self._original_httpx_send
            self._original_httpx_send = None
        if self._original_httpx_async_send:
            import httpx
            httpx.AsyncClient.send = self._original_httpx_async_send
            self._original_httpx_async_send = None
        if self._original_requests_send:
            import requests
            requests.Session.send = self._original_requests_send
            self._original_requests_send = None
