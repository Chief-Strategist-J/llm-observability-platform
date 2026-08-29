from __future__ import annotations

import json
import logging
from typing import Any, Callable
from confluent_kafka import Message
from src.shared.tracing.tracer import trace_span

logger = logging.getLogger(__name__)

class SpanConsumerHandler:
    def __init__(self, span_processor: Callable[[list[dict[str, Any]]], None]) -> None:
        self._span_processor = span_processor

    def __call__(self, message: Message) -> None:
        try:
            payload_bytes = message.value()
            if not payload_bytes:
                return
            data = json.loads(payload_bytes.decode("utf-8"))
            if isinstance(data, dict):
                spans = [data]
            elif isinstance(data, list):
                spans = data
            else:
                return

            first_span = spans[0] if isinstance(spans, list) and spans else {}
            trace_id = first_span.get("trace_id") if isinstance(first_span, dict) else None
            span_id = first_span.get("span_id") if isinstance(first_span, dict) else None

            with trace_span("span_consumer_handle_batch", trace_id=trace_id, span_id=span_id, attributes={
                "kafka.topic": message.topic() if hasattr(message, "topic") else "llm.spans.raw",
                "kafka.partition": message.partition() if hasattr(message, "partition") else 0,
                "kafka.offset": message.offset() if hasattr(message, "offset") else 0,
                "span_count": len(spans),
                "model": first_span.get("model", "unknown") if isinstance(first_span, dict) else "unknown"
            }):
                self._span_processor(spans)
        except Exception as exc:
            logger.error("SpanConsumerHandler failed to parse or process span message: %s", exc)
