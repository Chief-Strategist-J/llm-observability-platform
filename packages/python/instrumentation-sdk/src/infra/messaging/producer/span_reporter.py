from typing import Any, Dict
from src.features.spans.reporter import SpanReporter
from src.infra.messaging.producer.producer_adapter import KafkaProducerAdapter
from config.infra.env_config import service_config

class KafkaSpanReporter(SpanReporter):
    def __init__(self, topic: str = "llm.spans.raw"):
        self.producer_adapter = KafkaProducerAdapter()
        self.topic = topic

    def report(self, span_data: Dict[str, Any]) -> None:
        span_id = str(span_data.get("span_id", ""))
        self.producer_adapter.produce(self.topic, key=span_id, value=span_data)

    async def report_async(self, span_data: Dict[str, Any]) -> None:
        self.report(span_data)
