from typing import Callable, Any, Optional
from confluent_kafka import Producer
from src.shared.ports.kafka import KafkaProducerPort

class ConfluentKafkaProducerAdapter(KafkaProducerPort):
    def __init__(self, bootstrap_servers: str) -> None:
        self._producer = Producer({"bootstrap.servers": bootstrap_servers})

    def produce(
        self,
        topic: str,
        key: Any,
        value: Any,
        on_delivery: Optional[Callable[[Any, Any], None]] = None
    ) -> None:
        self._producer.produce(topic, key=key, value=value, on_delivery=on_delivery)

    def poll(self, timeout: float) -> int:
        return self._producer.poll(timeout)

    def flush(self, timeout: float) -> int:
        return self._producer.flush(timeout)

    def check_availability(self) -> bool:
        try:
            self._producer.list_topics(timeout=1.0)
            return True
        except Exception:
            return False
