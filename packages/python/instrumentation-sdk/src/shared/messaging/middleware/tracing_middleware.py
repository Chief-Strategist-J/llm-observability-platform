from typing import Dict, Any, Callable
from src.shared.messaging.tracing.messaging_tracer import messaging_tracer

def tracing_producer_middleware(topic: str, key: Any, value: Any, next_fn: Callable) -> None:
    event_name = value.get("event_name", "LLMSpan") if isinstance(value, dict) else "LLMSpan"
    correlation_id = value.get("correlation_id") if isinstance(value, dict) else None
    tenant_id = value.get("org_id") or value.get("tenant_id") if isinstance(value, dict) else None

    with messaging_tracer.start_producer_span(topic, event_name, correlation_id, tenant_id) as span:
        carrier = {}
        messaging_tracer.inject_context(carrier=carrier, headers={})
        next_fn(topic, key, value, carrier)

def tracing_consumer_middleware(message: Any, next_fn: Callable) -> Any:
    headers = getattr(message, "headers", [])
    topic = getattr(message, "topic", "unknown")
    event_name = "LLMSpan"

    with messaging_tracer.start_consumer_span(topic, event_name, headers) as span:
        return next_fn(message)
