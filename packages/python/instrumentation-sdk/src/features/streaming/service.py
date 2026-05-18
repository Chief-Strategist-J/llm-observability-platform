import time
from typing import Any, Callable, Optional
from ..manual_instrumentation.service import LLMSpanContext
from ..spans.globals import get_reporter
from .ports import TokenCounterPort, ObservableSpanPort

def default_extract_text(chunk: Any) -> str:
    if isinstance(chunk, str):
        return chunk
    if isinstance(chunk, dict):
        if "content" in chunk:
            return str(chunk["content"])
        choices = chunk.get("choices")
        if choices and isinstance(choices, list) and len(choices) > 0:
            delta = choices[0].get("delta", {})
            if isinstance(delta, dict) and "content" in delta:
                return str(delta["content"])
        return ""
    try:
        if hasattr(chunk, "choices"):
            choices = getattr(chunk, "choices")
            if choices and len(choices) > 0:
                delta = getattr(choices[0], "delta", None)
                if delta and hasattr(delta, "content"):
                    val = getattr(delta, "content")
                    return str(val) if val is not None else ""
        if hasattr(chunk, "content"):
            val = getattr(chunk, "content")
            return str(val) if val is not None else ""
    except Exception:
        pass
    return ""

class LLMStreamingSpanContext(LLMSpanContext):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._stream_finalized = False

    def __enter__(self) -> "LLMStreamingSpanContext":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    async def __aenter__(self) -> "LLMStreamingSpanContext":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    def finalize_stream(self, exc_type: Any = None) -> None:
        if self._stream_finalized:
            return
        self._stream_finalized = True
        self._finish(exc_type)
        reporter = get_reporter()
        reporter.report(self._data)

    async def finalize_stream_async(self, exc_type: Any = None) -> None:
        if self._stream_finalized:
            return
        self._stream_finalized = True
        self._finish(exc_type)
        reporter = get_reporter()
        await reporter.report_async(self._data)

class ObservableAsyncIterator:
    def __init__(
        self,
        async_iterable: Any,
        span_context: ObservableSpanPort,
        model: str,
        token_counter: TokenCounterPort,
        extract_text_fn: Optional[Callable[[Any], str]] = None
    ):
        self._async_iterator = async_iterable.__aiter__()
        self._span_context = span_context
        self._model = model
        self._token_counter = token_counter
        self._extract_text_fn = extract_text_fn or default_extract_text
        self._has_yielded = False
        self._accumulated_text = ""

    def __aiter__(self) -> "ObservableAsyncIterator":
        return self

    async def __anext__(self) -> Any:
        try:
            chunk = await self._async_iterator.__anext__()
            if not self._has_yielded:
                self._has_yielded = True
                ttft_ms = int((time.perf_counter() - self._span_context._start_time) * 1000)
                self._span_context.set_metadata("latency_ms_ttft", ttft_ms)

            text = self._extract_text_fn(chunk)
            self._accumulated_text += text
            tokens, method = self._token_counter.count_tokens(self._accumulated_text, self._model)
            self._span_context.set_metadata("completion_tokens", tokens)
            self._span_context.set_metadata("token_count_method", method)
            return chunk
        except StopAsyncIteration:
            await self._span_context.finalize_stream_async()
            raise
        except Exception as e:
            await self._span_context.finalize_stream_async(exc_type=type(e))
            raise

    async def aclose(self) -> None:
        if hasattr(self._async_iterator, "aclose"):
            try:
                await self._async_iterator.aclose()
            except Exception:
                pass
        await self._span_context.finalize_stream_async()

class ObservableIterator:
    def __init__(
        self,
        iterable: Any,
        span_context: ObservableSpanPort,
        model: str,
        token_counter: TokenCounterPort,
        extract_text_fn: Optional[Callable[[Any], str]] = None
    ):
        self._iterator = iter(iterable)
        self._span_context = span_context
        self._model = model
        self._token_counter = token_counter
        self._extract_text_fn = extract_text_fn or default_extract_text
        self._has_yielded = False
        self._accumulated_text = ""

    def __iter__(self) -> "ObservableIterator":
        return self

    def __next__(self) -> Any:
        try:
            chunk = next(self._iterator)
            if not self._has_yielded:
                self._has_yielded = True
                ttft_ms = int((time.perf_counter() - self._span_context._start_time) * 1000)
                self._span_context.set_metadata("latency_ms_ttft", ttft_ms)

            text = self._extract_text_fn(chunk)
            self._accumulated_text += text
            tokens, method = self._token_counter.count_tokens(self._accumulated_text, self._model)
            self._span_context.set_metadata("completion_tokens", tokens)
            self._span_context.set_metadata("token_count_method", method)
            return chunk
        except StopIteration:
            self._span_context.finalize_stream()
            raise
        except Exception as e:
            self._span_context.finalize_stream(exc_type=type(e))
            raise

    def close(self) -> None:
        if hasattr(self._iterator, "close"):
            try:
                self._iterator.close()
            except Exception:
                pass
        self._span_context.finalize_stream()

class StreamingService:
    def __init__(self, token_counter: TokenCounterPort):
        self._token_counter = token_counter

    def wrap_stream(
        self,
        iterable: Any,
        span_context: ObservableSpanPort,
        model: str,
        extract_text_fn: Optional[Callable[[Any], str]] = None
    ) -> ObservableIterator:
        return ObservableIterator(
            iterable=iterable,
            span_context=span_context,
            model=model,
            token_counter=self._token_counter,
            extract_text_fn=extract_text_fn
        )

    def wrap_async_stream(
        self,
        async_iterable: Any,
        span_context: ObservableSpanPort,
        model: str,
        extract_text_fn: Optional[Callable[[Any], str]] = None
    ) -> ObservableAsyncIterator:
        return ObservableAsyncIterator(
            async_iterable=async_iterable,
            span_context=span_context,
            model=model,
            token_counter=self._token_counter,
            extract_text_fn=extract_text_fn
        )
