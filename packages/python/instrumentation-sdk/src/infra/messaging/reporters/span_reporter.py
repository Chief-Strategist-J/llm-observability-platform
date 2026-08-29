from typing import Any, Dict, Optional
from src.features.spans.reporter import SpanReporter
from src.infra.messaging.producer.producer_client.kafka_producer_client import kafka_producer_client
from src.infra.messaging.topics.topic_provisioner import TopicProvisioner

class KafkaSpanReporter(SpanReporter):
    def __init__(self, topic: Optional[str] = None):
        self.producer_client = kafka_producer_client
        self.provisioner = TopicProvisioner()
        self.topic = topic or self.provisioner.resolve_event_topic("LLMSpan") or "llm.spans.raw"

    def report(self, span_data: Dict[str, Any]) -> None:
        span_id = str(span_data.get("span_id", ""))
        traceparent = span_data.get("traceparent", "")
        headers = {}
        if traceparent:
            headers["traceparent"] = traceparent
        if span_data.get("trace_id"):
            headers["trace_id"] = str(span_data.get("trace_id"))
        if hasattr(self.producer_client, "produce"):
            self.producer_client.produce(self.topic, key=span_id, value=span_data, headers=headers)
        elif hasattr(self.producer_client, "send_event"):
            self.producer_client.send_event(self.topic, key=span_id, value=span_data)

    async def report_async(self, span_data: Dict[str, Any]) -> None:
        self.report(span_data)
