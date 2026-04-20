from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

class BaseLLM(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_config = config.get("model", {})
        self.model_id = self.model_config.get("id")
        self.name = self.model_config.get("name", self.model_id)

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response for a given prompt."""
        pass

    @abstractmethod
    def stream_generate(self, prompt: str, **kwargs):
        """Stream the generation of a response."""
        pass

    @abstractmethod
    async def generate_async(self, prompt: str, **kwargs) -> str:
        """Asynchronously generate a response for a given prompt."""
        pass
    
    @abstractmethod
    async def astream_generate(self, prompt: str, **kwargs):
        """Asynchronously stream the generation of a response."""
        pass

    @abstractmethod
    def get_langchain_model(self) -> Any:
        """Return the underlying LangChain model instance if available."""
        pass
