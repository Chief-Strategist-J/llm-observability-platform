import pytest
import sys
from unittest.mock import MagicMock, AsyncMock, patch
from features.auto_instrumentation.index import init_auto_instrumentation, uninstrument_all
from features.spans.globals import set_reporter, NoOpReporter

@pytest.fixture
def mock_anthropic():
    mock_messages = MagicMock()
    mock_messages.create = AsyncMock(return_value=MagicMock(
        model="claude-3-5-sonnet",
        usage=MagicMock(input_tokens=15, output_tokens=25),
        stop_reason="end_turn",
        content=[MagicMock(text="hi")]
    ))
    
    with patch("importlib.util.find_spec", side_effect=lambda name: MagicMock() if name == "anthropic" else None):
        with patch.dict(sys.modules, {
            "anthropic": MagicMock(),
            "anthropic.resources": MagicMock(),
            "anthropic.resources.messages": MagicMock(AsyncMessages=mock_messages)
        }):
            yield mock_messages

@pytest.mark.asyncio
async def test_anthropic_auto_instrumentation(mock_anthropic):
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    
    try:
        init_auto_instrumentation()
        
        instance = MagicMock()
        await mock_anthropic.create(instance, model="claude-3-5-sonnet", messages=[{"role": "user", "content": "hi"}])
        
        assert mock_reporter.report_async.called
        span_data = mock_reporter.report_async.call_args[0][0]
        assert span_data["model"] == "claude-3-5-sonnet"
        assert span_data["provider"] == "anthropic"
        assert span_data["prompt_tokens"] == 15
    finally:
        uninstrument_all()
        set_reporter(NoOpReporter())
