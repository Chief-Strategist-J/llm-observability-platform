import pytest
import sys
from unittest.mock import MagicMock, AsyncMock, patch
from features.auto_instrumentation.index import init_auto_instrumentation, uninstrument_all
from features.spans.globals import set_reporter, NoOpReporter

@pytest.fixture
def mock_litellm():
    mock_litellm_mod = MagicMock()
    mock_litellm_mod.acompletion = AsyncMock(return_value=MagicMock(
        model="gpt-4o",
        usage=MagicMock(prompt_tokens=10, completion_tokens=20),
        choices=[MagicMock(finish_reason="stop", message=MagicMock(content="test"))]
    ))
    
    with patch("importlib.util.find_spec", side_effect=lambda name: MagicMock() if name == "litellm" else None):
        with patch.dict(sys.modules, {"litellm": mock_litellm_mod}):
            yield mock_litellm_mod

@pytest.mark.asyncio
async def test_litellm_auto_instrumentation(mock_litellm):
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    
    try:
        init_auto_instrumentation()
        
        await mock_litellm.acompletion(model="gpt-4o", messages=[{"role": "user", "content": "hi"}])
        
        assert mock_reporter.report_async.called
        span_data = mock_reporter.report_async.call_args[0][0]
        assert span_data["model"] == "gpt-4o"
        assert span_data["provider"] == "litellm"
    finally:
        uninstrument_all()
        set_reporter(NoOpReporter())
