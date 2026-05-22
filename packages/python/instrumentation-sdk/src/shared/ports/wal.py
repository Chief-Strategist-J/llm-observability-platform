from typing import Protocol, List, Tuple

class WalStoragePort(Protocol):
    def initialize(self) -> None:
        ...

    def save(self, span_id: str, span_json: str) -> None:
        ...

    def fetch_batch(self, limit: int) -> List[Tuple[int, str, str]]:
        ...

    def delete_batch(self, ids: List[int]) -> None:
        ...
