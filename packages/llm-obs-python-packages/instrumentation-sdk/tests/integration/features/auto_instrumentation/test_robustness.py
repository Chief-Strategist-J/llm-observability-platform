import pytest
import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from src.features.auto_instrumentation.index import init_auto_instrumentation, uninstrument_all
from src.features.spans.globals import set_reporter, NoOpReporter

@pytest.fixture
def mock_openai_module():
    mock_completions = MagicMock()
    
    async def dynamic_create(*args, **kwargs):
        model = kwargs.get("model", "gpt-4")
        return MagicMock(
            model=model,
            usage=MagicMock(prompt_tokens=10, completion_tokens=20),
            choices=[MagicMock(finish_reason="stop", message=MagicMock(content="test"))]
        )
        
    mock_completions.create = AsyncMock(side_effect=dynamic_create)
    
    with patch("importlib.util.find_spec", side_effect=lambda name: MagicMock() if name == "openai" else None):
        with patch.dict(sys.modules, {
            "openai": MagicMock(),
            "openai.resources": MagicMock(),
            "openai.resources.chat": MagicMock(),
            "openai.resources.chat.completions": MagicMock(AsyncCompletions=mock_completions)
        }):
            yield mock_completions

@pytest.mark.asyncio
async def test_openai_error_handling(mock_openai_module):
    # Test that if the LLM call fails, the span is still reported with error status
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    
    # Mock create to raise an error
    mock_openai_module.create.side_effect = Exception("API Error")
    
    try:
        init_auto_instrumentation()
        
        instance = MagicMock()
        with pytest.raises(Exception, match="API Error"):
            await mock_openai_module.create(instance, model="gpt-4", messages=[])
            
        assert mock_reporter.report_async.called
        span_data = mock_reporter.report_async.call_args[0][0]
        assert span_data["status"] == "error"
    finally:
        uninstrument_all()
        set_reporter(NoOpReporter())

@pytest.mark.asyncio
async def test_idempotency(mock_openai_module):
    # Calling init_auto_instrumentation twice should not double-patch
    init_auto_instrumentation()
    original_patched = mock_openai_module.create
    
    init_auto_instrumentation()
    assert mock_openai_module.create == original_patched
    
    uninstrument_all()

@pytest.mark.asyncio
async def test_concurrency_isolation(mock_openai_module):
    # Multiple concurrent calls should have separate spans
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    
    try:
        init_auto_instrumentation()
        
        instance = MagicMock()
        # Run two concurrent calls
        await asyncio.gather(
            mock_openai_module.create(instance, model="gpt-4-a", messages=[]),
            mock_openai_module.create(instance, model="gpt-4-b", messages=[])
        )
        
        assert mock_reporter.report_async.call_count == 2
        calls = [args[0][0]["model"] for args in mock_reporter.report_async.call_args_list]
        assert "gpt-4-a" in calls
        assert "gpt-4-b" in calls
    finally:
        uninstrument_all()
        set_reporter(NoOpReporter())

@pytest.mark.asyncio
async def test_uninstrument_restores_original(mock_openai_module):
    original = mock_openai_module.create
    
    init_auto_instrumentation()
    assert mock_openai_module.create != original
    
    uninstrument_all()
    # Note: In our current implementation, we restore by assignment.
    # Depending on how the mock was created, we check if it's the same object.
    from openai.resources.chat.completions import AsyncCompletions
    assert AsyncCompletions.create == original

@pytest.mark.asyncio
async def test_manual_client_instrumentation(mock_openai_module):
    # Test that instrument_client patches only the specific instance
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    
    try:
        # Create a "client" instance mock
        class MockClient:
            def __init__(self):
                self.chat = MagicMock()
                self.chat.completions = MagicMock()
                self.chat.completions.create = AsyncMock(return_value=MagicMock(
                    model="gpt-manual",
                    usage=MagicMock(prompt_tokens=5, completion_tokens=5),
                    choices=[MagicMock(finish_reason="stop", message=MagicMock(content="manual"))]
                ))
        
        client_instance = MockClient()
        from src.features.auto_instrumentation.index import instrument_client
        
        # Instrument ONLY this client
        instrument_client(client_instance, provider="openai")
        
        # Call the instance
        await client_instance.chat.completions.create(model="gpt-manual", messages=[])
        
        assert mock_reporter.report_async.called
        span_data = mock_reporter.report_async.call_args[0][0]
        assert span_data["model"] == "gpt-manual"
    finally:
        set_reporter(NoOpReporter())

@pytest.mark.asyncio
async def test_manual_instrumentation_multiple_providers(mock_openai_module):
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    
    try:
        from src.features.auto_instrumentation.index import instrument_client
        
        # Mock an Anthropic client
        mock_anthropic = MagicMock()
        mock_anthropic.messages = MagicMock()
        mock_anthropic.messages.create = AsyncMock(return_value=MagicMock(
            model="claude-manual",
            usage=MagicMock(input_tokens=1, output_tokens=1),
            stop_reason="end_turn",
            content=[MagicMock(text="hi")]
        ))
        
        # Mock OpenAI client
        mock_openai = MagicMock()
        mock_openai.chat = MagicMock()
        mock_openai.chat.completions = MagicMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=MagicMock(
            model="gpt-manual",
            usage=MagicMock(prompt_tokens=1, completion_tokens=1),
            choices=[MagicMock(finish_reason="stop", message=MagicMock(content="hi"))]
        ))
        
        # Patch them individually
        with patch("importlib.util.find_spec", side_effect=lambda name: MagicMock()):
            instrument_client(mock_openai, provider="openai")
            instrument_client(mock_anthropic, provider="anthropic")
            
        await mock_openai.chat.completions.create(model="gpt-manual", messages=[])
        await mock_anthropic.messages.create(model="claude-manual", messages=[])
        
        assert mock_reporter.report_async.call_count == 2
    finally:
        set_reporter(NoOpReporter())
