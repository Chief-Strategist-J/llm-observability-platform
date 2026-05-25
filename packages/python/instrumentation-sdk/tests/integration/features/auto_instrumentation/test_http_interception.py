import pytest
import sys
import json
from unittest.mock import MagicMock, patch, AsyncMock
from src.features.auto_instrumentation.index import init_auto_instrumentation, uninstrument_all
from src.features.spans.globals import set_reporter, NoOpReporter

@pytest.fixture
def mock_http_libs():
    mock_httpx = MagicMock()
    mock_httpx.AsyncClient.send = AsyncMock()
    mock_requests = MagicMock()
    
    with patch("importlib.util.find_spec", side_effect=lambda name: MagicMock() if name in ["httpx", "requests"] else None):
        with patch.dict(sys.modules, {
            "httpx": mock_httpx,
            "requests": mock_requests
        }):
            yield mock_httpx, mock_requests

def test_httpx_sync_interception(mock_http_libs):
    mock_httpx, _ = mock_http_libs
    mock_reporter = MagicMock()
    set_reporter(mock_reporter)
    
    try:
        init_auto_instrumentation()
        
        # Simulate an httpx request to OpenAI
        request = MagicMock()
        request.url = "https://api.openai.com/v1/chat/completions"
        request.content = json.dumps({"model": "gpt-custom-http"}).encode()
        
        client = MagicMock()
        mock_httpx.Client.send(client, request)
        
        assert mock_reporter.report.called
        span_data = mock_reporter.report.call_args[0][0]
        assert span_data["model"] == "gpt-custom-http"
        assert span_data["provider"] == "http:openai"
    finally:
        uninstrument_all()
        set_reporter(NoOpReporter())

@pytest.mark.asyncio
async def test_httpx_async_interception(mock_http_libs):
    mock_httpx, _ = mock_http_libs
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    
    try:
        init_auto_instrumentation()
        
        request = MagicMock()
        request.url = "https://api.openai.com/v1/chat/completions"
        request.content = json.dumps({"model": "gpt-async-http"}).encode()
        
        client = MagicMock()
        await mock_httpx.AsyncClient.send(client, request)
        
        assert mock_reporter.report_async.called
        span_data = mock_reporter.report_async.call_args[0][0]
        assert span_data["model"] == "gpt-async-http"
    finally:
        uninstrument_all()
        set_reporter(NoOpReporter())

def test_requests_interception(mock_http_libs):
    _, mock_requests = mock_http_libs
    mock_reporter = MagicMock()
    set_reporter(mock_reporter)
    
    try:
        init_auto_instrumentation()
        
        # Simulate a requests call to Anthropic
        request = MagicMock()
        request.url = "https://api.anthropic.com/v1/messages"
        request.body = json.dumps({"model": "claude-custom-http"})
        
        session = MagicMock()
        mock_requests.Session.send(session, request)
        
        assert mock_reporter.report.called
        span_data = mock_reporter.report.call_args[0][0]
        assert span_data["model"] == "claude-custom-http"
        assert span_data["provider"] == "http:anthropic"
    finally:
        uninstrument_all()
        set_reporter(NoOpReporter())
