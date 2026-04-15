from typing import Any, Dict
from services.llm.base.llm import BaseLLM
from services.llm.providers.local import LocalLLMProvider

class LLMFactory:
    """Factory for creating LLM providers."""
    
    @staticmethod
    def create(config: Dict[str, Any]) -> BaseLLM:
        """Create an LLM provider based on config."""
        model_config = config.get("model", {})
        provider_type = model_config.get("provider", "local")
        
        if provider_type == "local":
            return LocalLLMProvider(config)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
