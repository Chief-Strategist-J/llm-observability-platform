import pytest
import sys
from unittest.mock import MagicMock, AsyncMock, patch
from features.auto_instrumentation.index import init_auto_instrumentation, uninstrument_all
from features.spans.globals import set_reporter, NoOpReporter

@pytest.fixture
def mock_langchain():
    mock_base_model = MagicMock()
    mock_base_model.ainvoke = AsyncMock(return_value=MagicMock(
        usage_metadata={"input_tokens": 10, "output_tokens": 20}
    ))
    
    with patch("importlib.util.find_spec", side_effect=lambda name: MagicMock() if "langchain" in name else None):
        with patch.dict(sys.modules, {
            "langchain_core": MagicMock(),
            "langchain_core.language_models": MagicMock(),
            "langchain_core.language_models.chat_models": MagicMock(BaseChatModel=mock_base_model)
        }):
            yield mock_base_model

@pytest.mark.asyncio
async def test_langchain_auto_instrumentation(mock_langchain):
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    
    try:
        init_auto_instrumentation()
        
        instance = MagicMock()
        instance.model_name = "gpt-4"
        await mock_langchain.ainvoke(instance, "hi")
        
        assert mock_reporter.report_async.called
        span_data = mock_reporter.report_async.call_args[0][0]
        assert span_data["model"] == "gpt-4"
        assert "langchain" in span_data["provider"]
    finally:
        uninstrument_all()
        set_reporter(NoOpReporter())
