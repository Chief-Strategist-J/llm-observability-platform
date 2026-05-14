import json
from typing import Any, Dict
from confluent_kafka import Producer
from ...features.spans.reporter import SpanReporter
from .v1.llm.observability.v1.span_pb2 import LLMSpan

class KafkaSpanReporter(SpanReporter):
    def __init__(self, bootstrap_servers: str, topic: str = "llm.spans.raw"):
        self.producer = Producer({"bootstrap.servers": bootstrap_servers})
        self.topic = topic

    def report(self, span_data: Dict[str, Any]) -> None:
        span = LLMSpan(**span_data)
        self.producer.produce(
            self.topic, 
            key=span.span_id, 
            value=span.SerializeToString()
        )
        self.producer.flush()

    async def report_async(self, span_data: Dict[str, Any]) -> None:
        # For true async performance, we should use a non-blocking producer
        # but for this MVP, we wrap the sync call
        self.report(span_data)
