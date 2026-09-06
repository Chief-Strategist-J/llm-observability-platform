from __future__ import annotations

from typing import Any
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


def inject_trace_context(carrier: dict[str, str] | None = None) -> dict[str, str]:
    if carrier is None:
        carrier = {}
    TraceContextTextMapPropagator().inject(carrier)
    return carrier


def extract_trace_context(carrier: dict[str, Any] | list[tuple[str, bytes]] | None) -> Any:
    if carrier is None:
        return trace.get_current_span().get_span_context()
    
    headers_dict: dict[str, str] = {}
    if isinstance(carrier, dict):
        for k, v in carrier.items():
            headers_dict[k] = v.decode("utf-8") if isinstance(v, bytes) else str(v)
    elif isinstance(carrier, list):
        for k, v in carrier:
            headers_dict[k] = v.decode("utf-8") if isinstance(v, bytes) else str(v)

    return TraceContextTextMapPropagator().extract(carrier=headers_dict)
