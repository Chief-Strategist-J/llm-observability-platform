from typing import Dict, Optional
from .port import LlmProviderAdapterPort
from .google_adapter import GoogleGeminiAdapter
from .standard_adapters import OpenAIAdapter, AnthropicAdapter

class LlmProviderRegistry:
    _adapters: Dict[str, LlmProviderAdapterPort] = {}

    @classmethod
    def register(cls, adapter: LlmProviderAdapterPort) -> None:
        cls._adapters[adapter.provider_name().lower()] = adapter

    @classmethod
    def get(cls, provider_name: str) -> Optional[LlmProviderAdapterPort]:
        return cls._adapters.get(provider_name.lower())

# Auto-register core providers
LlmProviderRegistry.register(OpenAIAdapter())
LlmProviderRegistry.register(AnthropicAdapter())
LlmProviderRegistry.register(GoogleGeminiAdapter())
