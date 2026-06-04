from __future__ import annotations
from contextlib import contextmanager
from typing import Generator, Iterator
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource


def configure_tracer(service_name: str = "quality-engine") -> None:
    """Initialize OTEL TracerProvider with OTLP export if configured."""
    import os

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore[import-untyped]
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)


from opentelemetry.trace import SpanContext, TraceFlags

@contextmanager
def trace_span(
    name: str,
    trace_id: str | None = None,
    span_id: str | None = None,
    attributes: dict | None = None,
) -> Iterator[trace.Span]:
    tracer = trace.get_tracer("quality-engine")
    parent_ctx = None
    if trace_id and span_id:
        try:
            tid_val = int(trace_id, 16)
            sid_val = int(span_id, 16)
            sc = SpanContext(
                trace_id=tid_val,
                span_id=sid_val,
                is_remote=True,
                trace_flags=TraceFlags(0x01),
            )
            parent_ctx = trace.set_span_in_context(trace.NonRecordingSpan(sc))
        except ValueError:
            pass

    with tracer.start_as_current_span(name, context=parent_ctx) as span:
        if attributes:
            for k, v in attributes.items():
                if v is not None:
                    span.set_attribute(k, v)
        yield span

