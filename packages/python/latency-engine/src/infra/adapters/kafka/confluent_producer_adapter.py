from __future__ import annotations
import logging
import socket
from confluent_kafka import Producer  # type: ignore[import-untyped]
from shared.ports.kafka_producer_port import KafkaProducerPort

logger = logging.getLogger(__name__)

def is_kafka_alias_resolvable(bootstrap_servers: str) -> bool:
    try:
        parts = bootstrap_servers.split(",")[0].strip().split(":")
        host = parts[0]
        socket.gethostbyname(host)
        if host in ("localhost", "127.0.0.1"):
            socket.gethostbyname("llmobs-kafka-broker")
        return True
    except Exception:
        return False

class NoOpKafkaProducerAdapter(KafkaProducerPort):
    def produce(
        self,
        topic: str,
        key: str,
        value: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        pass

    def flush(self, timeout: float = 10.0) -> None:
        pass

class ConfluentKafkaProducerAdapter(KafkaProducerPort):
    def __init__(self, bootstrap_servers: str) -> None:
        self._producer = None
        if is_kafka_alias_resolvable(bootstrap_servers):
            try:
                self._producer = Producer({"bootstrap.servers": bootstrap_servers})
            except Exception as exc:
                logger.warning("Confluent Kafka Producer initialization failed: %s", exc)
        else:
            logger.info("Kafka broker internal alias unresolvable on host — using NoOp producer.")

    def produce(
        self,
        topic: str,
        key: str,
        value: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        if self._producer:
            self._producer.produce(
                topic=topic,
                key=key.encode(),
                value=value,
                headers=headers or {},
                on_delivery=_delivery_report,
            )

    def flush(self, timeout: float = 10.0) -> None:
        if self._producer:
            self._producer.flush(timeout=timeout)

def _delivery_report(err, msg) -> None:  # type: ignore[no-untyped-def]
    if err:
        logger.error(
            "kafka_delivery_failed topic=%s err=%s", msg.topic(), err
        )
