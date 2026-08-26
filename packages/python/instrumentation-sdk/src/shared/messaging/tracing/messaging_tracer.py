from typing import Dict, Any, List, Optional
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.trace import SpanKind, Status, StatusCode

tracer = trace.get_tracer("messaging.tracer")

class MessagingTracer:
    @staticmethod
    def inject_context(headers: Dict[str, Any], carrier_data: Optional[Dict[str, str]] = None) -> List[tuple]:
        carrier = dict(carrier_data or {})
        TraceContextTextMapPropagator().inject(carrier)
        header_tuples = list(headers.items()) if isinstance(headers, dict) else list(headers)
        header_tuples.extend([(k, v.encode("utf-8") if isinstance(v, str) else v) for k, v in carrier.items()])
        return header_tuples

    @staticmethod
    def extract_context(headers: Any) -> Any:
        carrier = {}
        if isinstance(headers, list):
            for k, v in headers:
                key_str = k.decode("utf-8") if isinstance(k, bytes) else str(k)
                val_str = v.decode("utf-8") if isinstance(v, bytes) else str(v)
                carrier[key_str] = val_str
        elif isinstance(headers, dict):
            carrier = {str(k): (v.decode("utf-8") if isinstance(v, bytes) else str(v)) for k, v in headers.items()}
        return TraceContextTextMapPropagator().extract(carrier)

    @staticmethod
    def start_producer_span(topic: str, event_name: str, correlation_id: Optional[str] = None, tenant_id: Optional[str] = None):
        span = tracer.start_span(
            name=f"{topic} send",
            kind=SpanKind.PRODUCER,
            attributes={
                "messaging.system": "kafka",
                "messaging.destination": topic,
                "messaging.destination_kind": "topic",
                "messaging.kafka.event_name": event_name,
                "messaging.correlation_id": str(correlation_id or ""),
                "messaging.tenant_id": str(tenant_id or ""),
            }
        )
        return span

    @staticmethod
    def start_consumer_span(topic: str, event_name: str, headers: Any):
        parent_context = MessagingTracer.extract_context(headers)
        span = tracer.start_span(
            name=f"{topic} receive",
            kind=SpanKind.CONSUMER,
            context=parent_context,
            attributes={
                "messaging.system": "kafka",
                "messaging.destination": topic,
                "messaging.destination_kind": "topic",
                "messaging.kafka.event_name": event_name,
            }
        )
        return span

messaging_tracer = MessagingTracer()
