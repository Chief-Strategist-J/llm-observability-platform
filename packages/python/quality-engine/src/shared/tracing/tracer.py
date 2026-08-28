from __future__ import annotations
import os
import socket
from contextlib import contextmanager
from typing import Iterator

from opentelemetry import trace
from opentelemetry.trace import SpanContext, TraceFlags, Span
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor, ConsoleSpanExporter

_PROVIDER_INITIALIZED = False


def configure_tracer(service_name: str = "quality-engine") -> None:
    """Initialize OTEL TracerProvider with OTLP export if configured."""
    init_tracer(service_name=service_name)


def init_tracer(service_name: str = "quality-engine") -> None:
    """Initialize OTEL TracerProvider (idempotent). Supports console + OTLP exporters."""
    global _PROVIDER_INITIALIZED
    if _PROVIDER_INITIALIZED:
        return

    resource = Resource.create({
        "service.name": service_name,
        "service.version": os.getenv("SERVICE_VERSION", "0.3.0"),
        "deployment.env": os.getenv("DEPLOYMENT_ENV", "dev"),
        "host.name": socket.gethostname(),
    })
    provider = TracerProvider(resource=resource)

    if os.getenv("SKIP_CONSOLE_EXPORTER") != "true":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint and os.getenv("SKIP_OTLP_EXPORTER") != "true":
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        except ImportError:
            pass

    trace.set_tracer_provider(provider)
    _PROVIDER_INITIALIZED = True


@contextmanager
def trace_span(
    name: str,
    trace_id: str | None = None,
    span_id: str | None = None,
    attributes: dict | None = None,
) -> Iterator[Span]:
    init_tracer()
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
        try:
            yield span
        except Exception as err:
            span.record_exception(err)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(err)))
            raise
