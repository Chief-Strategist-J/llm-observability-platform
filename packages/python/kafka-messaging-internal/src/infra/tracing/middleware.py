"""FastAPI tracing middleware with required span attributes."""

import os
import time
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from opentelemetry import trace, context
from opentelemetry.propagate import inject
from opentelemetry.trace.status import Status
from ..tracer import create_root_span, finish_span


class TracingMiddleware(BaseHTTPMiddleware):
    """Tracing middleware that creates root spans for all requests."""
    
    def __init__(self, app, dispatch: Callable = None):
        super().__init__(app, dispatch)
        self.tracer = trace.get_tracer(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Create root span for HTTP request."""
        # Extract traceparent from headers if present
        traceparent = request.headers.get("traceparent")
        if traceparent:
            ctx = context.extract(dict(traceparent=traceparent))
            token = context.attach(ctx)
        
        # Create root span
        operation_name = f"{request.method.lower()}_{request.url.path.replace('/', '_').strip('_') or 'root'}"
        span = create_root_span(
            operation_name=operation_name,
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.scheme": request.url.scheme,
                "http.host": request.url.hostname,
                "user_agent": request.headers.get("user-agent", ""),
                "api.version": "v1"
            }
        )
        
        # Add request-specific attributes
        span.set_attribute("feature.name", self._extract_feature_name(request))
        span.set_attribute("http.target", request.url.path)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record response attributes
            span.set_attribute("http.status_code", str(response.status_code))
            span.set_attribute("http.response_size", str(len(response.body) if hasattr(response, 'body') else 0))
            
            # Determine span status based on HTTP status
            if response.status_code >= 400:
                span.set_status(Status.ERROR)
                span.set_attribute("error.type", "http_error")
                span.set_attribute("error.message", f"HTTP {response.status_code}")
            else:
                span.set_status(Status.OK)
            
            return response
            
        except Exception as e:
            # Record error
            span.record_error(e)
            span.set_status(Status.ERROR)
            span.set_attribute("error.type", "application_error")
            span.set_attribute("error.message", str(e))
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "code": "SYSTEM_INTERNAL_ERROR",
                    "trace_id": span.get_span_context().trace_id
                }
            )
        
        finally:
            # Calculate and record duration
            duration = time.time() - start_time
            span.set_attribute("http.duration_ms", str(int(duration * 1000)))
            
            # Finish span
            finish_span(span)
            
            # Detach context if we attached it
            if traceparent:
                context.detach(token)
    
    def _extract_feature_name(self, request: Request) -> str:
        """Extract feature name from request path."""
        path = request.url.path
        
        if "/database" in path:
            return "database-operations"
        elif "/schema-registry" in path:
            return "schema-registry"
        elif "/event-handler" in path or "/event-processing" in path:
            return "event-processing"
        elif "/producer" in path or "/consumer" in path:
            return "messaging"
        else:
            return "unknown"


class RequestResponseLogger:
    """Helper for logging request/response details."""
    
    @staticmethod
    def log_request(span: trace.Span, request: Request):
        """Log request details to span."""
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.scheme", request.url.scheme)
        span.set_attribute("http.host", request.url.hostname)
        span.set_attribute("http.path", request.url.path)
        span.set_attribute("http.query", request.url.query)
        
        # Log headers (excluding sensitive ones)
        sensitive_headers = ['authorization', 'cookie', 'x-api-key']
        for key, value in request.headers.items():
            if key.lower() not in sensitive_headers:
                span.set_attribute(f"http.request.header.{key.lower()}", value)
    
    @staticmethod
    def log_response(span: trace.Span, response: Response):
        """Log response details to span."""
        span.set_attribute("http.status_code", str(response.status_code))
        span.set_attribute("http.response_size", str(len(response.body) if hasattr(response, 'body') else 0))
        
        # Log response headers
        if hasattr(response, 'headers'):
            for key, value in response.headers.items():
                span.set_attribute(f"http.response.header.{key.lower()}", value)
