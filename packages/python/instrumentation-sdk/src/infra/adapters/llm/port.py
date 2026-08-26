from typing import Protocol, Any, Dict, List, Optional
from src.features.spans.types import FinishReason

class LlmProviderAdapterPort(Protocol):
    def provider_name(self) -> str:
        ...

    def map_response(self, response: Any, model: Optional[str] = None) -> Dict[str, Any]:
        ...
