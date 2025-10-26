"""Example: Instrumented LLM Text Generation Use Case

This example shows how to add OpenTelemetry tracing, metrics, and logging
to an LLM text generation use case with graceful degradation.
"""

import logging
import time

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from ...telemetry import get_meter, get_tracer
from ..domain.models import LLMRequest, LLMResponse
from ..ports.llm_provider import LLMProviderPort

# Get telemetry instances
tracer = get_tracer(__name__)
meter = get_meter(__name__)

# Set up metrics (if available)
llm_requests_counter = None
llm_request_duration = None
llm_tokens_counter = None

if meter:
    # Request counter
    llm_requests_counter = meter.create_counter(
        name="llm_requests_total", description="Total number of LLM requests", unit="1"
    )

    # Request duration histogram
    llm_request_duration = meter.create_histogram(
        name="llm_request_duration_seconds",
        description="LLM request duration in seconds",
        unit="s",
    )

    # Token usage counter
    llm_tokens_counter = meter.create_counter(
        name="llm_tokens_total",
        description="Total number of tokens processed",
        unit="1",
    )


async def generate_text(
    request: LLMRequest,
    provider: LLMProviderPort,
    default_max_tokens: int,
    default_temperature: float,
) -> LLMResponse:
    """Generate text using LLM with comprehensive telemetry.

    This function demonstrates:
    - Distributed tracing with spans
    - Metrics collection (request count, duration, tokens)
    - Structured logging
    - Error handling and graceful degradation

    """
    start_time = time.time()

    # Create span for this operation
    span_name = f"llm.generate_text.{provider.__class__.__name__.lower()}"
    span_attributes = {
        "llm.provider": provider.__class__.__name__,
        "llm.model": getattr(request, "model", "unknown"),
        "llm.max_tokens": request.max_tokens or default_max_tokens,
        "llm.temperature": request.temperature or default_temperature,
        "user.id": getattr(request, "user_id", "anonymous"),
    }

    if tracer:
        # Create span with context
        with tracer.start_as_current_span(
            span_name, attributes=span_attributes, kind=trace.SpanKind.CLIENT
        ) as span:
            return await _generate_text_with_telemetry(
                request,
                provider,
                default_max_tokens,
                default_temperature,
                start_time,
                span,
            )
    else:
        # Fallback without tracing
        return await _generate_text_fallback(
            request,
            provider,
            default_max_tokens,
            default_temperature,
            start_time,
            span_attributes,
        )


async def _generate_text_with_telemetry(
    request: LLMRequest,
    provider: LLMProviderPort,
    default_max_tokens: int,
    default_temperature: float,
    start_time: float,
    span: trace.Span | None = None,
) -> LLMResponse:
    """
    Internal function with full telemetry support.
    """
    # Record request start
    if llm_requests_counter:
        llm_requests_counter.add(
            1,
            {
                "llm.provider": provider.__class__.__name__,
                "llm.model": getattr(request, "model", "unknown"),
                "status": "started",
            },
        )

    try:
        # Add span event for request start
        if span:
            span.add_event(
                "LLM request started",
                {
                    "prompt_length": len(request.prompt),
                    "max_tokens": request.max_tokens or default_max_tokens,
                },
            )

        # Make the actual LLM call
        response = await provider.generate(
            prompt=request.prompt,
            max_tokens=request.max_tokens or default_max_tokens,
            temperature=request.temperature or default_temperature,
        )

        # Calculate duration
        duration = time.time() - start_time

        # Record successful completion
        if llm_requests_counter:
            llm_requests_counter.add(
                1,
                {
                    "llm.provider": provider.__class__.__name__,
                    "llm.model": getattr(request, "model", "unknown"),
                    "status": "completed",
                },
            )

        # Record duration
        if llm_request_duration:
            llm_request_duration.record(
                duration,
                {
                    "llm.provider": provider.__class__.__name__,
                    "llm.model": getattr(request, "model", "unknown"),
                },
            )

        # Record token usage
        if llm_tokens_counter and hasattr(response, "usage"):
            prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
            completion_tokens = getattr(response.usage, "completion_tokens", 0)
            total_tokens = getattr(response.usage, "total_tokens", 0)

            llm_tokens_counter.add(
                prompt_tokens,
                {"llm.provider": provider.__class__.__name__, "token.type": "prompt"},
            )
            llm_tokens_counter.add(
                completion_tokens,
                {
                    "llm.provider": provider.__class__.__name__,
                    "token.type": "completion",
                },
            )
            llm_tokens_counter.add(
                total_tokens,
                {"llm.provider": provider.__class__.__name__, "token.type": "total"},
            )

        # Add span events for success
        if span:
            span.add_event(
                "LLM request completed",
                {
                    "response_length": len(response.text),
                    "duration_seconds": duration,
                    "total_tokens": getattr(response, "total_tokens", 0),
                },
            )

            # Set span status
            span.set_status(Status(StatusCode.OK))

        # Structured logging
        logging.info(
            "LLM text generation completed successfully",
            extra={
                "provider": provider.__class__.__name__,
                "model": getattr(request, "model", "unknown"),
                "duration_seconds": duration,
                "prompt_tokens": getattr(response, "prompt_tokens", 0),
                "completion_tokens": getattr(response, "completion_tokens", 0),
                "total_tokens": getattr(response, "total_tokens", 0),
            },
        )

        return response

    except Exception as e:
        duration = time.time() - start_time

        # Record failed request
        if llm_requests_counter:
            llm_requests_counter.add(
                1,
                {
                    "llm.provider": provider.__class__.__name__,
                    "llm.model": getattr(request, "model", "unknown"),
                    "status": "failed",
                },
            )

        # Record error duration
        if llm_request_duration:
            llm_request_duration.record(
                duration,
                {
                    "llm.provider": provider.__class__.__name__,
                    "llm.model": getattr(request, "model", "unknown"),
                    "error": "true",
                },
            )

        # Set span error status
        if span:
            span.add_event(
                "LLM request failed",
                {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "duration_seconds": duration,
                },
            )
            span.set_status(Status(StatusCode.ERROR, str(e)))

        # Error logging
        logging.error(
            "LLM text generation failed",
            extra={
                "provider": provider.__class__.__name__,
                "model": getattr(request, "model", "unknown"),
                "duration_seconds": duration,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )

        # Re-raise the exception
        raise


async def _generate_text_fallback(
    request: LLMRequest,
    provider: LLMProviderPort,
    default_max_tokens: int,
    default_temperature: float,
    start_time: float,
    span_attributes: dict,
) -> LLMResponse:
    """
    Fallback function when telemetry is not available.
    """
    try:
        # Simple logging without telemetry
        logging.info(
            "LLM text generation started (no telemetry)",
            extra={
                "provider": provider.__class__.__name__,
                "model": getattr(request, "model", "unknown"),
            },
        )

        response = await provider.generate(
            prompt=request.prompt,
            max_tokens=request.max_tokens or default_max_tokens,
            temperature=request.temperature or default_temperature,
        )

        duration = time.time() - start_time

        # Simple logging for success
        logging.info(
            "LLM text generation completed",
            extra={
                "provider": provider.__class__.__name__,
                "model": getattr(request, "model", "unknown"),
                "duration_seconds": duration,
            },
        )

        return response

    except Exception as e:
        duration = time.time() - start_time

        # Simple error logging
        logging.error(
            "LLM text generation failed",
            extra={
                "provider": provider.__class__.__name__,
                "model": getattr(request, "model", "unknown"),
                "duration_seconds": duration,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )

        raise
