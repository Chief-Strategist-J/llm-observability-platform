from __future__ import annotations
from confluent_kafka import Producer  # type: ignore[import-untyped]
from shared.ports.kafka_producer_port import KafkaProducerPort

class ConfluentKafkaProducerAdapter(KafkaProducerPort):
    def __init__(self, bootstrap_servers: str) -> None:
        self._producer = Producer({"bootstrap.servers": bootstrap_servers})

    def produce(
        self,
        topic: str,
        key: str,
        value: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._producer.produce(
            topic=topic,
            key=key.encode(),
            value=value,
            headers=headers or {},
            on_delivery=_delivery_report,
        )

    def flush(self, timeout: float = 10.0) -> None:
        self._producer.flush(timeout=timeout)

def _delivery_report(err, msg) -> None:  # type: ignore[no-untyped-def]
    import logging
    if err:
        logging.getLogger(__name__).error(
            "kafka_delivery_failed topic=%s err=%s", msg.topic(), err
        )
