import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from src import (
    llm_streaming_span,
    wrap_stream,
    wrap_async_stream,
    set_reporter
)
from src.features.spans.globals import NoOpReporter
from src.api.rest.v1.app import app

@pytest.fixture(autouse=True)
def mock_sync_thread():
    class SyncThread:
        def __init__(self, target, args=(), kwargs=None):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}
        def start(self):
            self.target(*self.args, **self.kwargs)
    with patch("threading.Thread", SyncThread):
        yield


def test_sync_streaming_success():
    mock_reporter = MagicMock()
    set_reporter(mock_reporter)
    try:
        chunks = ["Hello ", "world", "!"]
        span_ctx = llm_streaming_span(
            span_type="llm_call",
            provider="openai",
            model="gpt-4",
            prompt="Hello",
        )
        wrapped = wrap_stream(
            chunks,
            span_context=span_ctx,
            model="gpt-4"
        )
        res = list(wrapped)
        assert res == chunks
        assert mock_reporter.report.called
        data = mock_reporter.report.call_args[0][0]
        assert data["completion_tokens"] > 0
        assert "latency_ms_ttft" in data
        assert data["token_count_method"] == "tiktoken"
    finally:
        set_reporter(NoOpReporter())

@pytest.mark.asyncio
async def test_async_streaming_success():
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    try:
        chunks = ["Hello ", "world", "!"]
        async def mock_generator():
            for c in chunks:
                await asyncio.sleep(0.001)
                yield c

        span_ctx = llm_streaming_span(
            span_type="llm_call",
            provider="openai",
            model="gpt-4",
            prompt="Hello",
        )
        wrapped = wrap_async_stream(
            mock_generator(),
            span_context=span_ctx,
            model="gpt-4"
        )
        res = []
        async for chunk in wrapped:
            res.append(chunk)
        assert res == chunks
        assert mock_reporter.report_async.called
        data = mock_reporter.report_async.call_args[0][0]
        assert data["completion_tokens"] > 0
        assert "latency_ms_ttft" in data
        assert data["token_count_method"] == "tiktoken"
    finally:
        set_reporter(NoOpReporter())

def test_sync_streaming_exception():
    mock_reporter = MagicMock()
    set_reporter(mock_reporter)
    try:
        def err_generator():
            yield "first"
            raise ValueError("stream_error")

        span_ctx = llm_streaming_span(
            span_type="llm_call",
            provider="openai",
            model="gpt-4",
            prompt="Hello",
        )
        wrapped = wrap_stream(
            err_generator(),
            span_context=span_ctx,
            model="gpt-4"
        )
        res = []
        with pytest.raises(ValueError, match="stream_error"):
            for chunk in wrapped:
                res.append(chunk)
        assert res == ["first"]
        assert mock_reporter.report.called
    finally:
        set_reporter(NoOpReporter())

@pytest.mark.asyncio
async def test_async_streaming_exception():
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    try:
        async def err_generator():
            yield "first"
            raise ValueError("stream_error")

        span_ctx = llm_streaming_span(
            span_type="llm_call",
            provider="openai",
            model="gpt-4",
            prompt="Hello",
        )
        wrapped = wrap_async_stream(
            err_generator(),
            span_context=span_ctx,
            model="gpt-4"
        )
        res = []
        with pytest.raises(ValueError, match="stream_error"):
            async for chunk in wrapped:
                res.append(chunk)
        assert res == ["first"]
        assert mock_reporter.report_async.called
    finally:
        set_reporter(NoOpReporter())

def test_api_test_stream_call():
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    try:
        client = TestClient(app)
        response = client.post(
            "/v1/streaming/test-stream-call",
            json={"provider": "openai", "chunks": ["A", "B", "C"]}
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert response.text == "data: A\n\ndata: B\n\ndata: C\n\n"
        assert mock_reporter.report_async.called
    finally:
        set_reporter(NoOpReporter())

def test_empty_stream():
    mock_reporter = MagicMock()
    set_reporter(mock_reporter)
    try:
        span_ctx = llm_streaming_span(
            span_type="llm_call",
            provider="openai",
            model="gpt-4",
            prompt="Hello",
        )
        wrapped = wrap_stream(
            [],
            span_context=span_ctx,
            model="gpt-4"
        )
        res = list(wrapped)
        assert res == []
        assert mock_reporter.report.called
        data = mock_reporter.report.call_args[0][0]
        assert data.get("latency_ms_ttft") is None
        assert data.get("completion_tokens", 0) == 0
    finally:
        set_reporter(NoOpReporter())

@pytest.mark.asyncio
async def test_empty_stream_async():
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    try:
        async def empty_gen():
            if False:
                yield "never"
        span_ctx = llm_streaming_span(
            span_type="llm_call",
            provider="openai",
            model="gpt-4",
            prompt="Hello",
        )
        wrapped = wrap_async_stream(
            empty_gen(),
            span_context=span_ctx,
            model="gpt-4"
        )
        res = []
        async for chunk in wrapped:
            res.append(chunk)
        assert res == []
        assert mock_reporter.report_async.called
        data = mock_reporter.report_async.call_args[0][0]
        assert data.get("latency_ms_ttft") is None
        assert data.get("completion_tokens", 0) == 0
    finally:
        set_reporter(NoOpReporter())

def test_sync_stream_manual_close():
    mock_reporter = MagicMock()
    set_reporter(mock_reporter)
    try:
        def stream_gen():
            yield "first"
            yield "second"
            yield "third"
        span_ctx = llm_streaming_span(
            span_type="llm_call",
            provider="openai",
            model="gpt-4",
            prompt="Hello",
        )
        wrapped = wrap_stream(
            stream_gen(),
            span_context=span_ctx,
            model="gpt-4"
        )
        iterator = iter(wrapped)
        assert next(iterator) == "first"
        wrapped.close()
        assert mock_reporter.report.called
        data = mock_reporter.report.call_args[0][0]
        assert data["completion_tokens"] > 0
    finally:
        set_reporter(NoOpReporter())

@pytest.mark.asyncio
async def test_async_stream_manual_aclose():
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    try:
        async def stream_gen():
            yield "first"
            yield "second"
            yield "third"
        span_ctx = llm_streaming_span(
            span_type="llm_call",
            provider="openai",
            model="gpt-4",
            prompt="Hello",
        )
        wrapped = wrap_async_stream(
            stream_gen(),
            span_context=span_ctx,
            model="gpt-4"
        )
        iterator = wrapped.__aiter__()
        assert await iterator.__anext__() == "first"
        await wrapped.aclose()
        assert mock_reporter.report_async.called
        data = mock_reporter.report_async.call_args[0][0]
        assert data["completion_tokens"] > 0
    finally:
        set_reporter(NoOpReporter())

def test_mid_stream_metadata_updates():
    mock_reporter = MagicMock()
    set_reporter(mock_reporter)
    try:
        chunks = ["A", "B", "C"]
        span_ctx = llm_streaming_span(
            span_type="llm_call",
            provider="openai",
            model="gpt-4",
            prompt="Hello",
        )
        wrapped = wrap_stream(
            chunks,
            span_context=span_ctx,
            model="gpt-4"
        )
        for i, chunk in enumerate(wrapped):
            if i == 1:
                span_ctx.set_metadata("custom_field", "value_mid_stream")
        assert mock_reporter.report.called
        data = mock_reporter.report.call_args[0][0]
        assert data["custom_field"] == "value_mid_stream"
    finally:
        set_reporter(NoOpReporter())


def test_sync_extract_text_fn():
    mock_reporter = MagicMock()
    set_reporter(mock_reporter)
    try:
        chunks = [{"choices": [{"delta": {"content": "A"}}]}, {"choices": [{"delta": {"content": "B"}}]}]
        def extractor(chunk):
            return chunk["choices"][0]["delta"]["content"]
        span_ctx = llm_streaming_span(
            span_type="llm_call",
            provider="openai",
            model="gpt-4",
            prompt="Hello",
        )
        wrapped = wrap_stream(
            chunks,
            span_context=span_ctx,
            model="gpt-4",
            extract_text_fn=extractor
        )
        res = list(wrapped)
        assert res == chunks
        assert mock_reporter.report.called
        data = mock_reporter.report.call_args[0][0]
        assert data["completion_tokens"] == 1
    finally:
        set_reporter(NoOpReporter())


@pytest.mark.asyncio
async def test_async_extract_text_fn():
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    try:
        chunks = [{"choices": [{"delta": {"content": "X"}}]}, {"choices": [{"delta": {"content": "Y"}}]}]
        async def mock_generator():
            for c in chunks:
                yield c
        def extractor(chunk):
            return chunk["choices"][0]["delta"]["content"]
        span_ctx = llm_streaming_span(
            span_type="llm_call",
            provider="openai",
            model="gpt-4",
            prompt="Hello",
        )
        wrapped = wrap_async_stream(
            mock_generator(),
            span_context=span_ctx,
            model="gpt-4",
            extract_text_fn=extractor
        )
        res = []
        async for chunk in wrapped:
            res.append(chunk)
        assert res == chunks
        assert mock_reporter.report_async.called
        data = mock_reporter.report_async.call_args[0][0]
        assert data["completion_tokens"] == 1
    finally:
        set_reporter(NoOpReporter())


@pytest.mark.asyncio
async def test_multiple_stream_invocations_isolation():
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    try:
        async def gen1():
            yield "A"
            await asyncio.sleep(0.01)
            yield "B"

        async def gen2():
            yield "Y"
            await asyncio.sleep(0.01)
            yield "Z"

        ctx1 = llm_streaming_span(span_type="llm_call", provider="openai", model="gpt-4", prompt="Prompt 1")
        ctx2 = llm_streaming_span(span_type="llm_call", provider="openai", model="gpt-4", prompt="Prompt 2")

        w1 = wrap_async_stream(gen1(), span_context=ctx1, model="gpt-4")
        w2 = wrap_async_stream(gen2(), span_context=ctx2, model="gpt-4")

        res1, res2 = [], []
        async def run_w1():
            async for chunk in w1:
                res1.append(chunk)
        async def run_w2():
            async for chunk in w2:
                res2.append(chunk)

        await asyncio.gather(run_w1(), run_w2())

        assert res1 == ["A", "B"]
        assert res2 == ["Y", "Z"]
        assert mock_reporter.report_async.call_count == 2
        calls = [args[0][0] for args in mock_reporter.report_async.call_args_list]
        prompts = {c["prompt"] for c in calls}
        assert prompts == {"Prompt 1", "Prompt 2"}
    finally:
        set_reporter(NoOpReporter())


def test_heuristic_fallback_token_counting():
    mock_reporter = MagicMock()
    set_reporter(mock_reporter)
    try:
        chunks = ["chunk one ", "chunk two"]
        span_ctx = llm_streaming_span(
            span_type="llm_call",
            provider="anthropic",
            model="claude-3-opus",
            prompt="Hello",
        )
        wrapped = wrap_stream(
            chunks,
            span_context=span_ctx,
            model="claude-3-opus"
        )
        res = list(wrapped)
        assert res == chunks
        assert mock_reporter.report.called
        data = mock_reporter.report.call_args[0][0]
        assert data["token_count_method"] == "estimated"
        assert data["completion_tokens"] > 0
    finally:
        set_reporter(NoOpReporter())

