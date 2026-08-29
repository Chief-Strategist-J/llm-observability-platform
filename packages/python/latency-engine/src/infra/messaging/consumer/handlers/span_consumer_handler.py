from __future__ import annotations

import json
import logging
from typing import Any, Callable
from confluent_kafka import Message

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

            self._span_processor(spans)
        except Exception as exc:
            logger.error("SpanConsumerHandler failed to parse or process span message: %s", exc)
