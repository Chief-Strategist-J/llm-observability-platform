from __future__ import annotations
import os
import socket
from contextlib import contextmanager
from typing import Generator

from opentelemetry import trace
from opentelemetry.trace import Span, SpanContext, TraceFlags, Status, StatusCode
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

_PROVIDER_INITIALIZED = False
_SERVICE_NAME = "latency-engine"


def init_tracer(service_name: str = _SERVICE_NAME) -> None:
    """Initialize OTEL TracerProvider (idempotent). Supports console + OTLP exporters."""
    global _PROVIDER_INITIALIZED
    if _PROVIDER_INITIALIZED:
        return
    res = Resource.create({
        "service.name": service_name,
        "service.version": os.getenv("SERVICE_VERSION", "0.2.0"),
        "deployment.env": os.getenv("DEPLOYMENT_ENV", "dev"),
        "host.name": socket.gethostname(),
    })
    provider = TracerProvider(resource=res)
    if os.getenv("SKIP_CONSOLE_EXPORTER") != "true":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    if os.getenv("SKIP_OTLP_EXPORTER") != "true":
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
            provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True)))
        except ImportError:
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
                endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
                provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
            except ImportError:
                pass
    trace.set_tracer_provider(provider)
    _PROVIDER_INITIALIZED = True


@contextmanager
def trace_span(
    name: str,
    trace_id: str | None = None,
    span_id: str | None = None,
    attributes: dict[str, str | int | float | bool | None] | None = None,
) -> Generator[Span, None, None]:
    """
    Context manager for a named OTEL span. Supports optional parent context
    via trace_id/span_id. Used by baseline-worker Redis/ClickHouse adapters.
    """
    init_tracer()
    t = trace.get_tracer(_SERVICE_NAME)
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

    with t.start_as_current_span(name, context=parent_ctx) as span:
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


@contextmanager
def api_span(
    name: str,
    attributes: dict[str, str | int | float | bool] | None = None,
) -> Generator[Span, None, None]:
    """
    Context manager for API-layer OTEL spans. Always includes standard
    service.name, api.version, deployment.env attributes.
    Used by latency-engine REST handlers.
    """
    init_tracer()
    tracer = trace.get_tracer(_SERVICE_NAME)
    base_attrs: dict[str, str | int | float | bool] = {
        "service.name": _SERVICE_NAME,
        "api.version": "v1",
        "deployment.env": os.getenv("DEPLOYMENT_ENV", "dev"),
    }
    if attributes:
        base_attrs.update(attributes)

    with tracer.start_as_current_span(name, attributes=base_attrs) as span:
        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
