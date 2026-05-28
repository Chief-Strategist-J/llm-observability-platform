import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from worker.index import _extract_traceparent

def test_extract_traceparent_valid() -> None:
    headers = [
        ("traceparent", b"00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"),
        ("tracestate", b"rojo=1,congo=2")
    ]
    context = _extract_traceparent(headers)
    assert context is not None

    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("test-tracer")

    with tracer.start_as_current_span("test-span", context=context):
        pass

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    
    assert format(span.context.trace_id, "032x") == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert span.parent is not None
    assert format(span.parent.span_id, "016x") == "00f067aa0ba902b7"

def test_extract_traceparent_none() -> None:
    assert _extract_traceparent(None) is None
    assert _extract_traceparent([]) is None
    assert _extract_traceparent([("other-header", b"value")]) is None

def test_handler_sub_spans() -> None:
    import opentelemetry.trace as otel_trace
    current_provider = otel_trace.get_tracer_provider()
    if hasattr(current_provider, "_delegate"):
        current_provider = current_provider._delegate
        
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    
    if hasattr(current_provider, "add_span_processor"):
        current_provider.add_span_processor(processor)
    
    from unittest.mock import MagicMock
    from handlers.alerts_budget.handler import BudgetAlertHandler
    
    db_port = MagicMock()
    redis_port = MagicMock()
    slack_port = MagicMock()
    metrics_port = MagicMock()
    
    redis_port.acquire_rate_limit.return_value = True
    
    import os
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("service_owners:\n  default: owner_a\n")
        temp_path = f.name
        
    try:
        handler = BudgetAlertHandler(
            db_port=db_port,
            redis_port=redis_port,
            slack_port=slack_port,
            metrics_port=metrics_port,
            service_owners_path=temp_path
        )
        
        payload = {
            "user_id": "user123",
            "model": "gpt-4",
            "event_type": "blocked",
            "service": "default",
            "timestamp_utc": "2026-05-28T10:00:00Z"
        }
        
        handler.handle(payload)
        
        spans = exporter.get_finished_spans()
        assert len(spans) > 0
        
        span_names = [s.name for s in spans]
        assert "budget_alert_handler.handle" in span_names
        assert "budget_alert_handler.check_rate_limit" in span_names
        assert "budget_alert_handler.insert_database" in span_names
        assert "budget_alert_handler.notify_slack_channel" in span_names
        
    finally:
        os.unlink(temp_path)


