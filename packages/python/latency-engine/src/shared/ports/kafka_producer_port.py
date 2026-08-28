from __future__ import annotations
from typing import Protocol

class KafkaProducerPort(Protocol):
    def produce(
        self,
        topic: str,
        key: str,
        value: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        ...

    def flush(self, timeout: float = 10.0) -> None:
        ...
