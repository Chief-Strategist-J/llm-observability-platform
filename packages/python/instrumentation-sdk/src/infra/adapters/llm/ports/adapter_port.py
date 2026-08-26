from typing import Protocol, Any, Dict, Optional

class LlmProviderAdapterPort(Protocol):
    def provider_name(self) -> str:
        ...

    def map_response(self, response: Any, model: Optional[str] = None) -> Dict[str, Any]:
        ...
