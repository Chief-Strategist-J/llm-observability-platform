import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from src import (
    llm_streaming_span,
    wrap_stream,
    wrap_async_stream,
    set_reporter
)
from src.features.spans.globals import NoOpReporter
from src.api.rest.v1.app import app

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

