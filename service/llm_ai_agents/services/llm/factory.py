from typing import Any, Dict
from services.llm.base.llm import BaseLLM
from services.llm.registry import PROVIDER_REGISTRY
from services.shared.exceptions import ProviderNotFoundError


class LLMFactory:
    @staticmethod
    def create(config: Dict[str, Any]) -> BaseLLM:
        provider_type = config.get("model", {}).get("provider", "local")
        provider_class = PROVIDER_REGISTRY.get(provider_type)
        if provider_class is None:
            raise ProviderNotFoundError(f"Unknown provider: {provider_type}")
        return provider_class(config)
