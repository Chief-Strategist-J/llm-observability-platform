from typing import Protocol, Any, List

class TokenEncoderPort(Protocol):
    def get_encoding(self, model: str) -> Any:
        ...

    def encode(self, encoding: Any, text: str) -> List[int]:
        ...
