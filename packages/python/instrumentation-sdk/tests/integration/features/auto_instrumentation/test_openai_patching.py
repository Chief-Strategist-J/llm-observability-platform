import pytest
import sys
from unittest.mock import MagicMock, AsyncMock, patch
from features.auto_instrumentation.index import init_auto_instrumentation, uninstrument_all
from features.spans.globals import get_reporter

@pytest.fixture
def mock_openai():
    # Create a mock for the entire openai package structure needed
    mock_completions = MagicMock()
    mock_completions.create = AsyncMock(return_value=MagicMock(
        model="gpt-4",
        usage=MagicMock(prompt_tokens=10, completion_tokens=20),
        choices=[MagicMock(finish_reason="stop", message=MagicMock(content="test"))]
    ))
    
    # Mock find_spec to return something for "openai"
    with patch("importlib.util.find_spec", side_effect=lambda name: MagicMock() if name == "openai" else None):
        with patch.dict(sys.modules, {
            "openai": MagicMock(),
            "openai.resources": MagicMock(),
            "openai.resources.chat": MagicMock(),
            "openai.resources.chat.completions": MagicMock(AsyncCompletions=mock_completions)
        }):
            yield mock_completions

@pytest.mark.asyncio
async def test_openai_auto_instrumentation(mock_openai):
    # Setup mock reporter
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    
    from features.spans.globals import set_reporter, NoOpReporter
    set_reporter(mock_reporter)
    
    try:
        # Initialize instrumentation
        init_auto_instrumentation()
        
        # Verify it was patched
        assert mock_openai.create != mock_openai.create.__wrapped__ if hasattr(mock_openai.create, "__wrapped__") else True
        
        # Call the patched method
        instance = MagicMock()
        await mock_openai.create(instance, model="gpt-4", messages=[{"role": "user", "content": "hi"}])
        
        # Verify reporter was called
        assert mock_reporter.report_async.called
        span_data = mock_reporter.report_async.call_args[0][0]
        assert span_data["model"] == "gpt-4"
        assert span_data["provider"] == "openai"
    finally:
        # Clean up
        uninstrument_all()
        set_reporter(NoOpReporter())
