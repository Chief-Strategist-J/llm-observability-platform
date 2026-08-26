from typing import Callable, Any, Optional
from src.shared.ports.kafka import KafkaProducerPort
from src.infra.messaging.producer.producer_factory import kafka_producer_factory

class KafkaPythonProducerAdapter(KafkaProducerPort):
    def __init__(self) -> None:
        self._factory = kafka_producer_factory

    def produce(
        self,
        topic: str,
        key: Any,
        value: Any,
        on_delivery: Optional[Callable[[Any, Any], None]] = None
    ) -> None:
        producer = self._factory.get_producer()
        key_bytes = key.encode("utf-8") if isinstance(key, str) else key
        future = producer.send(topic, key=key_bytes, value=value)
        if on_delivery:
            def _on_success(record_metadata):
                on_delivery(None, record_metadata)
            def _on_err(exc):
                on_delivery(exc, None)
            future.add_callback(_on_success).add_errback(_on_err)

    def poll(self, timeout: float) -> int:
        return 0

    def flush(self, timeout: float) -> int:
        producer = self._factory.get_producer()
        producer.flush(timeout=timeout)
        return 0

    def check_availability(self) -> bool:
        try:
            producer = self._factory.get_producer()
            return producer.bootstrap_connected()
        except Exception:
            return False
