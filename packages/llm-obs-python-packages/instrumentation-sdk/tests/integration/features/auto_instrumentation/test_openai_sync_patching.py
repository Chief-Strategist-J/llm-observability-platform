import pytest
import sys
from unittest.mock import MagicMock, patch
from src.features.auto_instrumentation.index import init_auto_instrumentation, uninstrument_all
from src.features.spans.globals import set_reporter, NoOpReporter

@pytest.fixture
def mock_openai_sync():
    mock_completions = MagicMock()
    
    def dynamic_create(*args, **kwargs):
        model = kwargs.get("model", "gpt-4")
        return MagicMock(
            model=model,
            usage=MagicMock(prompt_tokens=10, completion_tokens=20),
            choices=[MagicMock(finish_reason="stop", message=MagicMock(content="sync-test"))]
        )
        
    mock_completions.create.side_effect = dynamic_create
    
    with patch("importlib.util.find_spec", side_effect=lambda name: MagicMock() if name == "openai" else None):
        with patch.dict(sys.modules, {
            "openai": MagicMock(),
            "openai.resources": MagicMock(),
            "openai.resources.chat": MagicMock(),
            "openai.resources.chat.completions": MagicMock(Completions=mock_completions, AsyncCompletions=MagicMock())
        }):
            yield mock_completions

def test_openai_sync_auto_instrumentation(mock_openai_sync):
    mock_reporter = MagicMock()
    set_reporter(mock_reporter)
    
    try:
        init_auto_instrumentation()
        
        instance = MagicMock()
        mock_openai_sync.create(instance, model="gpt-4-sync", messages=[])
        
        assert mock_reporter.report.called
        span_data = mock_reporter.report.call_args[0][0]
        assert span_data["model"] == "gpt-4-sync"
        assert span_data["provider"] == "openai"
    finally:
        uninstrument_all()
        set_reporter(NoOpReporter())
