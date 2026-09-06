from __future__ import annotations
import functools
import logging
from typing import Callable, Any
from shared.tracing.tracer import get_tracer

logger = logging.getLogger(__name__)

def handle_repository_errors(default_factory: Callable[[], Any] | Any = None):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                tracer = get_tracer()
                span = tracer.start_span(f"repository.error.{func.__name__}")
                span.record_exception(exc)
                span.end()
                logger.error("Repository execution %s failed: %s", func.__name__, exc)
                return default_factory() if callable(default_factory) else default_factory
        return wrapper
    return decorator
