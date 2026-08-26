from typing import Any, Dict
from src.features.spans.reporter import SpanReporter
from src.infra.messaging.producer.producer_client.kafka_producer_client import kafka_producer_client

class KafkaSpanReporter(SpanReporter):
    def __init__(self, topic: str = "llm.spans.raw"):
        self.producer_client = kafka_producer_client
        self.topic = topic

    def report(self, span_data: Dict[str, Any]) -> None:
        span_id = str(span_data.get("span_id", ""))
        self.producer_client.send_event(self.topic, key=span_id, value=span_data)

    async def report_async(self, span_data: Dict[str, Any]) -> None:
        self.report(span_data)
