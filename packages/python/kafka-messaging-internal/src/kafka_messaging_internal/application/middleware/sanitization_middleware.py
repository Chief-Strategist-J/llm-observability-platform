"""Input sanitization middleware."""

import re
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from opentelemetry import trace

from shared.errors.codes import validation_failed

_tracer = trace.get_tracer(__name__)


async def sanitization_middleware(request: Request, call_next: Callable) -> Response:
    """Input sanitization middleware with tracing."""
    with _tracer.start_as_current_span("sanitization_middleware") as span:
        span.set_attribute("service.name", "kafka-messaging-internal")
        span.set_attribute("feature.name", "sanitization")
        span.set_attribute("api.version", "v1")
        
        try:
            # Sanitize query parameters
            if request.query_params:
                sanitized_query = {}
                for key, value in request.query_params.items():
                    if isinstance(value, str):
                        # Basic SQL injection prevention
                        sanitized_value = re.sub(r'[\'";\\]', '', value)
                        # Basic XSS prevention  
                        sanitized_value = re.sub(r'[<>]', '', sanitized_value)
                        sanitized_query[key] = sanitized_value
                    else:
                        sanitized_query[key] = value
                
                # Override query params
                request._query_params = sanitized_query
            
            # Sanitize headers
            if request.headers:
                sanitized_headers = {}
                for key, value in request.headers.items():
                    # Remove potentially dangerous headers
                    if key.lower() not in ['host', 'x-forwarded-for', 'x-real-ip']:
                        sanitized_headers[key] = value
                
                # Override headers
                request._headers = sanitized_headers
            
            span.set_attribute("sanitization.result", "success")
            return await call_next(request)
            
        except Exception as e:
            span.record_error(e)
            span.set_attribute("sanitization.result", "error")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input data"
            )
