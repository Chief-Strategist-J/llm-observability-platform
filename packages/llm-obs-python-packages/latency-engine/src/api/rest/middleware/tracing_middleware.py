from __future__ import annotations

import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from infra.messaging.tracing.context_propagation import extract_trace_context
from shared.tracing.tracer import get_tracer
from opentelemetry.trace import format_trace_id

logger = logging.getLogger(__name__)

class HTTPTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        traceparent = request.headers.get("traceparent")
        x_trace_id = request.headers.get("x-trace-id")
        
        headers_dict = dict(request.headers)
        parent_ctx = extract_trace_context(headers_dict)
        
        span_name = f"http.request.{request.method} {request.url.path}"
        
        tracer = get_tracer()
        with tracer.start_as_current_span(span_name, context=parent_ctx) as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.route", request.url.path)
            
            sc = span.get_span_context()
            trace_id_str = format_trace_id(sc.trace_id) if sc and sc.trace_id else x_trace_id
            
            try:
                response: Response = await call_next(request)
                span.set_attribute("http.status_code", response.status_code)
                if trace_id_str:
                    response.headers["x-trace-id"] = trace_id_str
                return response
            except Exception as exc:
                span.record_exception(exc)
                logger.exception("HTTP Request failed: %s", exc)
                raise exc
