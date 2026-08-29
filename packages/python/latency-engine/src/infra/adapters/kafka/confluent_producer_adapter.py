"""
Algorithm Summary: Confluent Kafka Producer Adapter.
Provides direct Kafka message delivery via confluent_kafka Producer driver.
Checks host resolution using central Kafka constants without hardcoded strings or static host names.
Applies @traced_adapter to capture trace_id, span context, and delivery telemetry automatically.
"""
from __future__ import annotations
import logging
import socket
from typing import Any
from confluent_kafka import Producer  # type: ignore[import-untyped]
from shared.ports.kafka_producer_port import KafkaProducerPort
from shared.constants.kafka_constants import kafka_constants
from shared.tracing.tracer import traced_adapter

logger = logging.getLogger(__name__)

def is_kafka_alias_resolvable(bootstrap_servers: str) -> bool:
    try:
        host = bootstrap_servers.split(",")[0].strip().split(":")[0]
        socket.gethostbyname(host)
        host in kafka_constants.LOCAL_HOSTNAMES and socket.gethostbyname(kafka_constants.KAFKA_BROKER_ALIAS)
        return True
    except Exception:
        return False

def _delivery_report(err: Any, msg: Any) -> None:
    err and logger.error("kafka_delivery_failed topic=%s err=%s", msg.topic(), err)

class NoOpKafkaProducerAdapter(KafkaProducerPort):
    def produce(
        self,
        topic: str,
        key: str,
        value: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        pass

    def flush(self, timeout: float = kafka_constants.DEFAULT_FLUSH_TIMEOUT_SEC) -> None:
        pass

class ConfluentKafkaProducerAdapter(KafkaProducerPort):
    def __init__(self, bootstrap_servers: str) -> None:
        self._producer = None
        is_kafka_alias_resolvable(bootstrap_servers) and self._init_producer(bootstrap_servers)

    def _init_producer(self, bootstrap_servers: str) -> None:
        try:
            self._producer = Producer({kafka_constants.BOOTSTRAP_SERVERS_KEY: bootstrap_servers})
        except Exception as exc:
            logger.warning("Confluent Kafka Producer initialization failed: %s", exc)

    @traced_adapter("kafka")
    def produce(
        self,
        topic: str,
        key: str,
        value: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._producer and self._producer.produce(
            topic=topic,
            key=key.encode(),
            value=value,
            headers=headers or {},
            on_delivery=_delivery_report,
        )

    @traced_adapter("kafka")
    def flush(self, timeout: float = kafka_constants.DEFAULT_FLUSH_TIMEOUT_SEC) -> None:
        self._producer and self._producer.flush(timeout=timeout)
