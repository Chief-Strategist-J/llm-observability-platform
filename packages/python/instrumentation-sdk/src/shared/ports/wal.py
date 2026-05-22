from typing import Protocol, List, Tuple, Any

class WalStoragePort(Protocol):
    def initialize(self) -> None:
        ...

    def save(self, span_id: str, span_json: str) -> None:
        ...

    def save_batch(self, spans: List[Tuple[str, Any]]) -> None:
        ...

    def fetch_batch(self, limit: int) -> List[Tuple[int, str, Any]]:
        ...

    def delete_batch(self, ids: List[int]) -> None:
        ...

