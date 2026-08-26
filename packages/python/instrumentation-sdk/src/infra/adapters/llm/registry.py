from typing import Dict, Optional
from .ports.adapter_port import LlmProviderAdapterPort
from .implementations.google_adapter import GoogleGeminiAdapter
from .implementations.standard_adapters import OpenAIAdapter, AnthropicAdapter

class LlmProviderRegistry:
    _adapters: Dict[str, LlmProviderAdapterPort] = {}

    @classmethod
    def register(cls, adapter: LlmProviderAdapterPort) -> None:
        cls._adapters[adapter.provider_name().lower()] = adapter

    @classmethod
    def get(cls, provider_name: str) -> Optional[LlmProviderAdapterPort]:
        return cls._adapters.get(provider_name.lower())

# Auto-register core provider implementations
LlmProviderRegistry.register(OpenAIAdapter())
LlmProviderRegistry.register(AnthropicAdapter())
LlmProviderRegistry.register(GoogleGeminiAdapter())
