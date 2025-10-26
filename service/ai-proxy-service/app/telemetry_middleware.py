"""Example: FastAPI Middleware with OpenTelemetry Integration

This example shows how to add OpenTelemetry middleware to a FastAPI application
with graceful degradation when observability services are unavailable.
"""

from collections.abc import Callable
import logging
import time

from fastapi import Request, Response
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from starlette.middleware.base import BaseHTTPMiddleware

from ...telemetry import get_meter, get_tracer

# Get telemetry instances
tracer = get_tracer(__name__)
meter = get_meter(__name__)

# Set up metrics (if available)
http_requests_counter = None
http_request_duration = None

if meter:
    # HTTP request counter
    http_requests_counter = meter.create_counter(
        name="http_requests_total",
        description="Total number of HTTP requests",
        unit="1",
    )

    # HTTP request duration histogram
    http_request_duration = meter.create_histogram(
        name="http_request_duration_seconds",
        description="HTTP request duration in seconds",
        unit="s",
    )


class TelemetryMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic telemetry collection.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with telemetry.
        """
        start_time = time.time()
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "unknown")

        # Create span attributes
        span_attributes = {
            "http.method": method,
            "http.url": str(request.url),
            "http.user_agent": user_agent,
            "http.route": path,
        }

        # Record request
        if http_requests_counter:
            http_requests_counter.add(1, {**span_attributes, "status": "started"})

        if tracer:
            # Create span for HTTP request
            span_name = f"HTTP {method} {path}"
            with tracer.start_as_current_span(
                span_name, attributes=span_attributes, kind=trace.SpanKind.SERVER
            ) as span:
                return await self._dispatch_with_tracing(
                    request, call_next, start_time, span
                )
        else:
            # Fallback without tracing
            return await self._dispatch_fallback(
                request, call_next, start_time, span_attributes
            )

    async def _dispatch_with_tracing(
        self, request: Request, call_next: Callable, start_time: float, span: trace.Span
    ) -> Response:
        """
        Dispatch with full tracing support.
        """
        try:
            # Process the request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Update span with response info
            span.set_attribute("http.status_code", response.status_code)
            span.add_event(
                "HTTP request completed",
                {
                    "status_code": response.status_code,
                    "duration_seconds": duration,
                },
            )

            # Record successful request
            if http_requests_counter:
                http_requests_counter.add(
                    1,
                    {
                        "http.method": request.method,
                        "http.url": str(request.url),
                        "http.status_code": response.status_code,
                        "status": "completed",
                    },
                )

            # Record duration
            if http_request_duration:
                http_request_duration.record(
                    duration,
                    {
                        "http.method": request.method,
                        "http.status_code": response.status_code,
                    },
                )

            # Set span status based on HTTP status code
            if response.status_code < 400:
                span.set_status(Status(StatusCode.OK))
            else:
                span.set_status(
                    Status(StatusCode.ERROR, f"HTTP {response.status_code}")
                )

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Record failed request
            if http_requests_counter:
                http_requests_counter.add(
                    1,
                    {
                        "http.method": request.method,
                        "http.url": str(request.url),
                        "error": "true",
                        "status": "failed",
                    },
                )

            # Record error duration
            if http_request_duration:
                http_request_duration.record(
                    duration, {"http.method": request.method, "error": "true"}
                )

            # Set span error
            span.add_event(
                "HTTP request failed",
                {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "duration_seconds": duration,
                },
            )
            span.set_status(Status(StatusCode.ERROR, str(e)))

            # Re-raise the exception
            raise

    async def _dispatch_fallback(
        self,
        request: Request,
        call_next: Callable,
        start_time: float,
        span_attributes: dict,
    ) -> Response:
        """
        Dispatch fallback when telemetry is not available.
        """
        try:
            # Simple logging
            logging.info(
                "HTTP request started (no telemetry)",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "user_agent": request.headers.get("user-agent", "unknown"),
                },
            )

            response = await call_next(request)
            duration = time.time() - start_time

            # Simple success logging
            logging.info(
                "HTTP request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_seconds": duration,
                },
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Simple error logging
            logging.error(
                "HTTP request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_seconds": duration,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )

            raise


async def initialize_telemetry_for_service(
    service_name: str = "ai-proxy-service",
    service_version: str = "1.0.0",
) -> bool:
    """Initialize telemetry for the AI Proxy service.

    This function should be called during application startup. It handles graceful
    degradation when observability services are not available.

    """
    import os

    from ...telemetry import initialize_telemetry

    # Get environment configuration
    environment = os.getenv("ENVIRONMENT", "development")

    # Initialize telemetry with graceful degradation
    success = initialize_telemetry(
        service_name=service_name,
        service_version=service_version,
        environment=environment,
        enable_tracing=True,
        enable_metrics=True,
        enable_logging=True,
        sampling_ratio=(
            1.0 if environment == "development" else 0.1
        ),  # Lower sampling in production
    )

    if success:
        logging.info(f"Telemetry initialized successfully for {service_name}")
    else:
        logging.warning(
            f"Telemetry initialization completed with degraded functionality for {service_name}"
        )

    return success


async def shutdown_telemetry_for_service() -> None:
    """
    Shutdown telemetry for the service.
    """
    from ...telemetry import shutdown_telemetry

    shutdown_telemetry()
    logging.info("Telemetry shutdown completed")


def create_instrumented_app(app_title: str = "AI Proxy Service", **kwargs) -> FastAPI:
    """Create a FastAPI application with telemetry middleware.

    Args:
        app_title: Title for the FastAPI application
        **kwargs: Additional arguments for FastAPI

    Returns:
        FastAPI application with telemetry middleware

    """
    from fastapi import FastAPI

    # Create FastAPI app
    app = FastAPI(title=app_title, **kwargs)

    # Add telemetry middleware (if telemetry is available)
    if tracer or meter:
        app.add_middleware(TelemetryMiddleware)
        logging.info("Telemetry middleware added to FastAPI app")
    else:
        logging.warning("Telemetry not available, running without middleware")

    return app
