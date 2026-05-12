"""Auth middleware with OTEL tracing."""

import logging
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from shared.errors.codes import authentication_failed

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware with single responsibility"""
    
    def __init__(self, app, api_key: Optional[str] = None, skip_paths: Optional[list] = None):
        super().__init__(app)
        self._api_key = api_key
        self._skip_paths = skip_paths or ["/health", "/metrics", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        with _tracer.start_as_current_span("auth_middleware") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "auth-middleware")
            span.set_attribute("api.version", "v1")
            span.set_attribute("http.path", request.url.path)
            
            try:
                if self._should_skip(request.url.path):
                    span.set_attribute("auth.skipped", "true")
                    return await call_next(request)

                auth_header = request.headers.get("Authorization")
                api_key_header = request.headers.get("X-API-Key")

                if not self._api_key:
                    span.set_attribute("auth.configured", "false")
                    logger.warning("Auth middleware enabled but no API key configured")
                    return await call_next(request)

                span.set_attribute("auth.configured", "true")
                
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                    if token == self._api_key:
                        span.set_attribute("auth.result", "success")
                        span.set_attribute("auth.method", "bearer")
                        return await call_next(request)
                
                if api_key_header and api_key_header == self._api_key:
                    span.set_attribute("auth.result", "success")
                    span.set_attribute("auth.method", "api-key")
                    return await call_next(request)

                span.set_attribute("auth.result", "failed")
                span.set_status(Status(StatusCode.ERROR, "Authentication failed"))
                logger.warning("Authentication failed for path: %s", request.url.path)
                raise authentication_failed("Invalid or missing authentication credentials")
                
            except HTTPException:
                raise
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("auth.result", "error")
                logger.error("Auth middleware error: %s", str(e))
                raise authentication_failed(f"Authentication error: {str(e)}")

    def _should_skip(self, path: str) -> bool:
        """Check if path should be skipped"""
        return any(path.startswith(skip_path) for skip_path in self._skip_paths)
