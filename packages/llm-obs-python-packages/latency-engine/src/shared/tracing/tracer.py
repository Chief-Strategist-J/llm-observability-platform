from __future__ import annotations
import os
import socket
import logging
import functools
from contextlib import contextmanager
from typing import Generator, Callable, Any

from opentelemetry import trace
from opentelemetry.trace import Span, SpanContext, TraceFlags, Status, StatusCode
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

logging.getLogger("opentelemetry.exporter.otlp.proto.grpc.exporter").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.sdk.trace").setLevel(logging.CRITICAL)

_PROVIDER_INITIALIZED = False
_SERVICE_NAME = "latency-engine"

def _is_otel_reachable(host: str = "localhost", port: int = 31423) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except Exception:
        return False

def init_tracer(service_name: str = _SERVICE_NAME) -> None:
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
    
    if os.getenv("SKIP_CONSOLE_EXPORTER", "true") == "false":
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        
    if os.getenv("SKIP_OTLP_EXPORTER", "true") != "true" and _is_otel_reachable():
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:31423")
        grpc_target = endpoint.replace("http://", "").replace("https://", "")
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=grpc_target, insecure=True)))
        except Exception:
            pass

    trace.set_tracer_provider(provider)
    _PROVIDER_INITIALIZED = True

def get_tracer():
    init_tracer()
    return trace.get_tracer(_SERVICE_NAME)

def traced_adapter(system: str = "adapter"):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            tracer = get_tracer()
            span_name = f"{system}:{func.__name__}"
            with tracer.start_as_current_span(span_name) as span:
                ctx = span.get_span_context()
                trace_id_hex = f"{ctx.trace_id:032x}" if ctx and ctx.trace_id else ""
                span_id_hex = f"{ctx.span_id:016x}" if ctx and ctx.span_id else ""

                span.set_attribute("db.system", system)
                span.set_attribute("db.operation", func.__name__)
                span.set_attribute("trace_id", trace_id_hex)
                span.set_attribute("span_id", span_id_hex)

                for idx, arg in enumerate(args):
                    span.set_attribute(f"arg.{idx}", str(arg))
                for k, v in kwargs.items():
                    span.set_attribute(f"param.{k}", str(v))

                try:
                    result = func(self, *args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as exc:
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                    raise
        return wrapper
    return decorator

@contextmanager
def trace_span(
    name: str,
    trace_id: str | None = None,
    span_id: str | None = None,
    attributes: dict[str, str | int | float | bool | None] | None = None,
) -> Generator[Span, None, None]:
    init_tracer()
    t = get_tracer()
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
        ctx = span.get_span_context()
        if ctx and ctx.trace_id:
            span.set_attribute("trace_id", f"{ctx.trace_id:032x}")
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
    trace_id: str | None = None,
    span_id: str | None = None,
) -> Generator[Span, None, None]:
    init_tracer()
    tracer = get_tracer()
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

    base_attrs: dict[str, str | int | float | bool] = {
        "service.name": _SERVICE_NAME,
        "api.version": "v1",
        "deployment.env": os.getenv("DEPLOYMENT_ENV", "dev"),
    }
    if attributes:
        base_attrs.update(attributes)

    with tracer.start_as_current_span(name, context=parent_ctx, attributes=base_attrs) as span:
        ctx = span.get_span_context()
        if ctx and ctx.trace_id:
            span.set_attribute("trace_id", f"{ctx.trace_id:032x}")
        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
