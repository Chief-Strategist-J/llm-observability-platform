import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import sys
from features.auto_instrumentation.index import init_auto_instrumentation, uninstrument_all
from features.spans.globals import set_reporter, NoOpReporter

@pytest.fixture
def mock_openai_sdk():
    mock_completions = MagicMock()
    async def mock_create(*args, **kwargs):
        return MagicMock(
            model="gpt-sdk",
            usage=MagicMock(prompt_tokens=10, completion_tokens=10),
            choices=[MagicMock(finish_reason="stop", message=MagicMock(content="sdk"))]
        )
    mock_completions.create = AsyncMock(side_effect=mock_create)
    
    with patch.dict(sys.modules, {
        "openai": MagicMock(),
        "openai.resources": MagicMock(),
        "openai.resources.chat": MagicMock(),
        "openai.resources.chat.completions": MagicMock(AsyncCompletions=mock_completions)
    }):
        yield mock_completions

@pytest.fixture
def mock_http_lib():
    mock_httpx = MagicMock()
    mock_httpx.AsyncClient.send = AsyncMock()
    mock_openai = MagicMock()
    # Mock as package
    mock_openai.__path__ = []
    with patch("importlib.util.find_spec", side_effect=lambda name: MagicMock() if name in ["httpx", "openai", "openai.resources", "openai.resources.chat", "openai.resources.chat.completions"] else None):
        with patch.dict(sys.modules, {
            "httpx": mock_httpx, 
            "openai": mock_openai,
            "openai.resources": MagicMock(),
            "openai.resources.chat": MagicMock(),
            "openai.resources.chat.completions": MagicMock()
        }):
            yield mock_httpx

@pytest.mark.asyncio
async def test_sdk_and_http_patcher_interop(mock_openai_sdk, mock_http_lib):
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    
    try:
        init_auto_instrumentation()
        
        # 1. Call via SDK (should trigger SDK patcher)
        instance = MagicMock()
        await mock_openai_sdk.create(instance, model="gpt-sdk", messages=[])
        
        assert mock_reporter.report_async.called
        # Note: Since we mocked the SDK call and it didn't trigger an actual HTTP call in this test,
        # only the SDK span should be reported.
        assert mock_reporter.report_async.call_count == 1
        
    finally:
        uninstrument_all()
        set_reporter(NoOpReporter())

@pytest.mark.asyncio
async def test_http_patcher_fallback_when_sdk_unsupported(mock_http_lib):
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    
    try:
        init_auto_instrumentation()
        
        # Simulate an httpx request
        request = MagicMock()
        request.url = "https://api.openai.com/v1/chat/completions"
        request.content = b'{"model": "fallback-model"}'
        
        client = MagicMock()
        await mock_http_lib.AsyncClient.send(client, request)
                
        assert mock_reporter.report_async.called
        span = mock_reporter.report_async.call_args[0][0]
        assert span["provider"] == "http:openai"
        assert span["model"] == "fallback-model"
    finally:
        uninstrument_all()
        set_reporter(NoOpReporter())
