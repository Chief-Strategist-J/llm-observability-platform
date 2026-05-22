from typing import Protocol, Callable, Any, Optional

class KafkaProducerPort(Protocol):
    def produce(
        self,
        topic: str,
        key: Any,
        value: Any,
        on_delivery: Optional[Callable[[Any, Any], None]] = None
    ) -> None:
        ...

    def poll(self, timeout: float) -> int:
        ...

    def flush(self, timeout: float) -> int:
        ...

    def check_availability(self) -> bool:
        ...
