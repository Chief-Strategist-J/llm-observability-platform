from .service import AutoInstrumentationService
from .infra.patchers.openai_patcher import OpenAIPatcher
from .infra.patchers.anthropic_patcher import AnthropicPatcher
from .infra.patchers.litellm_patcher import LiteLLMPatcher
from .infra.patchers.langchain_patcher import LangChainPatcher
from .infra.patchers.http_patcher import HTTPPatcher

from typing import Dict, Any, Optional

_SERVICE = AutoInstrumentationService(
    patchers=[
        OpenAIPatcher(),
        AnthropicPatcher(),
        LiteLLMPatcher(),
        LangChainPatcher(),
        HTTPPatcher()
    ]
)

def init_auto_instrumentation() -> None:
    _SERVICE.instrument_all()

def uninstrument_all() -> None:
    _SERVICE.uninstrument_all()

def instrument_client(client: Any, provider: str) -> None:
    _SERVICE.instrument_client(client, provider)

def instrument_http_client(client: Any, provider: Optional[str] = None) -> None:
    for patcher in _SERVICE._patchers:
        if isinstance(patcher, HTTPPatcher):
            patcher.patch_instance(client)
            return

def detect_llm_call(url: str, body: str) -> Dict[str, str]:
    for patcher in _SERVICE._patchers:
        if isinstance(patcher, HTTPPatcher):
            provider = patcher._detect_provider(url)
            model = patcher._extract_model(body)
            return {"provider": provider or "unknown", "model": model}
    return {"provider": "unknown", "model": "unknown"}

async def trigger_test_call(method: str, provider: str) -> Dict[str, Any]:
    import httpx
    import json
    
    url_map = {
        "openai": "https://api.openai.com/v1/chat/completions",
        "anthropic": "https://api.anthropic.com/v1/messages"
    }
    url = url_map.get(provider, "https://api.openai.com/v1/chat/completions")
    payload = {"model": "instrumentation-test-model"}
    
    try:
        if method == "httpx":
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(url, json=payload, timeout=1.0)
                except httpx.HTTPError:
                    pass
        elif method == "requests":
            import requests
            try:
                requests.post(url, json=payload, timeout=1.0)
            except requests.RequestException:
                pass
        
        return {"success": True, "message": f"Test call triggered via {method} for {provider}"}
    except Exception as e:
        return {"success": False, "message": str(e)}
