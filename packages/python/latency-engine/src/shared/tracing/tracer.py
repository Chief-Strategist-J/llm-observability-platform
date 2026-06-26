from __future__ import annotations

import os
import socket
from contextlib import contextmanager
from typing import Generator

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

_PROVIDER_INITIALIZED = False
_SERVICE_NAME = "latency-engine"


def init_tracer() -> None:
    global _PROVIDER_INITIALIZED
    if _PROVIDER_INITIALIZED:
        return
    res = Resource.create({
        "service.name": _SERVICE_NAME,
        "service.version": "0.1.0",
        "deployment.env": os.getenv("DEPLOYMENT_ENV", "dev"),
        "host.name": socket.gethostname(),
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
def api_span(
    name: str,
    attributes: dict[str, str | int | float | bool] | None = None,
) -> Generator[Span, None, None]:
    """
    Context manager that opens a named OTEL span with standard latency-engine
    attributes. Records exceptions and sets ERROR status automatically.
    Always calls span.end() in the finally block.
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
