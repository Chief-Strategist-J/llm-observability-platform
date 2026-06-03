from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from opentelemetry import trace
from opentelemetry.trace import SpanContext, TraceFlags, Span
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

_PROVIDER_INITIALIZED = False

def init_tracer() -> None:
    global _PROVIDER_INITIALIZED
    if _PROVIDER_INITIALIZED:
        return
    res = Resource.create({
        "service.name": "toxicity-worker",
        "service.version": "0.1.0",
        "deployment.env": os.getenv("DEPLOYMENT_ENV", "dev"),
    })
    prov = TracerProvider(resource=res)
    if os.getenv("SKIP_CONSOLE_EXPORTER") != "true":
        prov.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    if os.getenv("SKIP_OTLP_EXPORTER") != "true":
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
            prov.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True)))
        except ImportError:
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
                endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
                prov.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
            except ImportError:
                pass
    trace.set_tracer_provider(prov)
    _PROVIDER_INITIALIZED = True

@contextmanager
def trace_span(
    name: str,
    trace_id: str | None = None,
    span_id: str | None = None,
    attributes: dict[str, str | int | float | bool | None] | None = None,
) -> Generator[Span, None, None]:
    init_tracer()
    t = trace.get_tracer("toxicity-worker")

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
