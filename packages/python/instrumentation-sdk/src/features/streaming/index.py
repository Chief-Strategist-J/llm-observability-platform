from typing import Any, Callable, Optional
from .infra.adapters.token_counter_adapter import TokenCounterAdapter
from .service import StreamingService, LLMStreamingSpanContext, ObservableIterator, ObservableAsyncIterator

_ADAPTER = TokenCounterAdapter()
_SERVICE = StreamingService(token_counter=_ADAPTER)

def llm_streaming_span(**kwargs: Any) -> LLMStreamingSpanContext:
    return LLMStreamingSpanContext(**kwargs)

def wrap_stream(
    iterable: Any,
    span_context: Any,
    model: str,
    extract_text_fn: Optional[Callable[[Any], str]] = None
) -> ObservableIterator:
    return _SERVICE.wrap_stream(iterable, span_context, model, extract_text_fn)

def wrap_async_stream(
    async_iterable: Any,
    span_context: Any,
    model: str,
    extract_text_fn: Optional[Callable[[Any], str]] = None
) -> ObservableAsyncIterator:
    return _SERVICE.wrap_async_stream(async_iterable, span_context, model, extract_text_fn)
