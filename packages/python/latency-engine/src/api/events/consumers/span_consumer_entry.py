from __future__ import annotations

from typing import Callable, Any
from infra.messaging.consumer.factory.consumer_factory import ConsumerFactory
from infra.messaging.consumer.handlers.span_consumer_handler import SpanConsumerHandler


class SpanConsumerEntry:
    def __init__(self, group_id: str = "latency-engine-cg", topic: str = "llm.spans.raw") -> None:
        self.group_id = group_id
        self.topic = topic

    def start(self, processor: Callable[[list[dict[str, Any]]], None], should_stop: Callable[[], bool] | None = None) -> None:
        handler = SpanConsumerHandler(processor)
        client = ConsumerFactory.create_client(self.group_id, [self.topic])
        client.consume_loop(handler=handler, should_stop=should_stop)
