"""Logging middleware with tracing."""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from opentelemetry import trace

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """Logging middleware with request tracing."""
    with _tracer.start_as_current_span("logging_middleware") as span:
        span.set_attribute("service.name", "kafka-messaging-internal")
        span.set_attribute("feature.name", "logging")
        span.set_attribute("api.version", "v1")
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.user_agent", request.headers.get("user-agent", "unknown"))
        
        start_time = time.time()
        
        try:
            # Log request start
            logger.info(
                "event=request_start method=%s url=%s",
                request.method,
                str(request.url)
            )
            
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Add response attributes to span
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.duration_ms", duration_ms)
            
            # Log request completion
            logger.info(
                "event=request_complete method=%s url=%s status=%d duration_ms=%d",
                request.method,
                str(request.url),
                response.status_code,
                duration_ms
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Record error on span
            span.record_error(e)
            span.set_attribute("http.status_code", 500)
            span.set_attribute("http.duration_ms", duration_ms)
            
            # Log request error
            logger.error(
                "event=request_error method=%s url=%s duration_ms=%d error=%s",
                request.method,
                str(request.url),
                duration_ms,
                str(e)
            )
            
            raise
