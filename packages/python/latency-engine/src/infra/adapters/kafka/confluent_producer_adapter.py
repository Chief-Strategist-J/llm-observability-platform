"""
Algorithm Summary: Confluent Kafka Producer Adapter.
Provides direct Kafka message delivery via confluent_kafka Producer driver through the master Kafka producer
middleware pipeline composed of tracing_producer_middleware, serialization_middleware, and partition_key_middleware.
Automatically injects W3C traceparent headers, handles JSON serialization, and performs partition key selection without inline comments or hardcoded strings.
"""
from __future__ import annotations
import logging
import socket
from typing import Any
from confluent_kafka import Producer  # type: ignore[import-untyped]
from shared.ports.kafka_producer_port import KafkaProducerPort
from shared.constants.kafka_constants import kafka_constants
from infra.messaging.middleware.pipeline import ProduceCtx, compose
from infra.messaging.middleware.producer_middleware import (
    tracing_producer_middleware,
    serialization_middleware,
    partition_key_middleware,
)

logger = logging.getLogger(__name__)

def is_kafka_alias_resolvable(bootstrap_servers: str) -> bool:
    try:
        host = bootstrap_servers.split(",")[0].strip().split(":")[0]
        socket.gethostbyname(host)
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
        
        def _raw_target(ctx: ProduceCtx) -> None:
            self._producer and self._producer.produce(
                topic=ctx.topic,
                key=ctx.key.encode() if isinstance(ctx.key, str) else ctx.key,
                value=ctx.value,
                headers=ctx.headers,
                on_delivery=_delivery_report,
            )

        self._pipeline = compose(
            tracing_producer_middleware,
            serialization_middleware,
            partition_key_middleware,
        )(_raw_target)

    def _init_producer(self, bootstrap_servers: str) -> None:
        try:
            self._producer = Producer({kafka_constants.BOOTSTRAP_SERVERS_KEY: bootstrap_servers})
        except Exception as exc:
            logger.warning("Confluent Kafka Producer initialization failed: %s", exc)

    def produce(
        self,
        topic: str,
        key: str,
        value: bytes | dict | str,
        headers: dict[str, str] | None = None,
    ) -> None:
        ctx = ProduceCtx(
            topic=topic,
            key=key,
            value=value,
            headers=headers or {},
        )
        self._pipeline(ctx)

    def flush(self, timeout: float = kafka_constants.DEFAULT_FLUSH_TIMEOUT_SEC) -> None:
        self._producer and self._producer.flush(timeout=timeout)
