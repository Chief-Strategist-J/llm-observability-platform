"""
Algorithm Summary: Managed Kafka Producer Client.
Encapsulates confluent_kafka Producer instance with master Kafka producer middleware pipeline composed via compose.
Executes tracing_producer_middleware, serialization_middleware, and partition_key_middleware for all produce operations.
Automatically injects W3C traceparent headers and enforces partition key selection without inline comments or static strings.
"""
from __future__ import annotations
import logging
from typing import Any, Callable
from confluent_kafka import Producer, KafkaError
from infra.messaging.middleware.pipeline import ProduceCtx, compose
from infra.messaging.middleware.producer_middleware import (
    tracing_producer_middleware,
    serialization_middleware,
    partition_key_middleware,
)
from shared.constants.kafka_constants import kafka_constants

logger = logging.getLogger(__name__)

class KafkaProducerClient:
    def __init__(self, producer: Producer) -> None:
        self._producer = producer

        def _raw_target(ctx: ProduceCtx) -> None:
            def _delivery_cb(err: KafkaError | None, msg: Any) -> None:
                err and logger.error("Kafka produce failed to topic %s: %s", ctx.topic, err)

            header_list = list(map(
                lambda kv: (kv[0], kv[1].encode("utf-8") if isinstance(kv[1], str) else kv[1]),
                ctx.headers.items()
            ))

            self._producer.produce(
                topic=ctx.topic,
                value=ctx.value,
                key=ctx.key.encode() if isinstance(ctx.key, str) else ctx.key,
                headers=header_list,
                callback=_delivery_cb,
            )
            self._producer.poll(0)

        self._pipeline = compose(
            tracing_producer_middleware,
            serialization_middleware,
            partition_key_middleware,
        )(_raw_target)

    def produce(
        self,
        topic: str,
        value: dict[str, Any] | str | bytes,
        key: str | bytes | None = None,
        headers: dict[str, str | bytes] | None = None,
    ) -> None:
        dict_headers = dict(headers) if isinstance(headers, (dict, list)) else {}
        ctx = ProduceCtx(
            topic=topic,
            key=key,
            value=value,
            headers=dict_headers,
        )
        self._pipeline(ctx)

    def flush(self, timeout: float = kafka_constants.DEFAULT_FLUSH_TIMEOUT_SEC) -> int:
        return self._producer.flush(timeout)
