"""
Pure functional tracing module for observability client

This module provides functional, composable tracing utilities.
"""

from typing import Dict, Any, ContextManager
from contextlib import contextmanager
from opentelemetry import trace
from opentelemetry.trace import Tracer, Span


# Type aliases
SpanAttributes = Dict[str, Any]


def create_span(
    tracer: Tracer,
    name: str,
    attributes: SpanAttributes = None
) -> Span:
    """
    Create a new span
    
    Pure function: Creates a span instrument
    """
    span = tracer.start_span(name)
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    return span


def set_span_attributes(span: Span, attributes: SpanAttributes) -> None:
    """
    Set attributes on a span
    
    Pure action: Predictable side effect
    """
    for key, value in attributes.items():
        span.set_attribute(key, value)


def set_span_status(span: Span, status_code, description: str = None) -> None:
    """
    Set span status
    
    Pure action: Predictable side effect
    """
    if description:
        span.set_status(status_code, description)
    else:
        span.set_status(status_code)


@contextmanager
def span_context(
    tracer: Tracer,
    name: str,
    attributes: SpanAttributes = None
):
    """
    Context manager for creating and managing spans
    
    Functional context manager
    """
    span = create_span(tracer, name, attributes)
    try:
        yield span
    except Exception as e:
        span.record_exception(e)
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
        raise
    finally:
        span.end()


class TracerClient:
    """
    Tracer client with functional core
    
    Provides convenient API while keeping core logic functional
    """
    
    def __init__(self, tracer: Tracer):
        self.tracer = tracer
    
    def start_span(
        self,
        name: str,
        attributes: SpanAttributes = None
    ) -> Span:
        """Start a new span"""
        return create_span(self.tracer, name, attributes)
    
    def start_as_current_span(
        self,
        name: str,
        attributes: SpanAttributes = None
    ) -> ContextManager[Span]:
        """Start a span as current context"""
        return span_context(self.tracer, name, attributes)
