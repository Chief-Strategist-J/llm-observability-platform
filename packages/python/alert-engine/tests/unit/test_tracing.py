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
