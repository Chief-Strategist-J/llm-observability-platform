from __future__ import annotations

import logging
from typing import Any, Callable
from confluent_kafka import Message
from infra.messaging.middleware.pipeline import ConsumeCtx, compose
from infra.messaging.middleware.tracing_middleware import tracing_consumer_middleware
from infra.messaging.middleware.consumer_middleware import deserialization_middleware

logger = logging.getLogger(__name__)

class SpanConsumerHandler:
    def __init__(self, span_processor: Callable[[list[dict[str, Any]]], None]) -> None:
        self._span_processor = span_processor
        
        def _target(ctx: ConsumeCtx) -> None:
            if ctx.payload and isinstance(ctx.payload, list):
                self._span_processor(ctx.payload)
            elif ctx.payload and isinstance(ctx.payload, dict):
                self._span_processor([ctx.payload])

        self._pipeline = compose(
            [deserialization_middleware, tracing_consumer_middleware],
            _target
        )

    def __call__(self, message: Message) -> None:
        try:
            headers_dict: dict[str, str] = {}
            if hasattr(message, "headers") and message.headers():
                for k, v in message.headers():
                    headers_dict[k] = v.decode("utf-8") if isinstance(v, bytes) else str(v)

            ctx = ConsumeCtx(
                topic=message.topic() if hasattr(message, "topic") else "llm.spans.raw",
                partition=message.partition() if hasattr(message, "partition") else 0,
                offset=message.offset() if hasattr(message, "offset") else 0,
                key=message.key() if hasattr(message, "key") else None,
                raw_value=message.value() if hasattr(message, "value") else None,
                headers=headers_dict,
            )
            self._pipeline(ctx)
        except Exception as exc:
            logger.error("SpanConsumerHandler failed in middleware pipeline: %s", exc)
