import pytest
from unittest.mock import MagicMock
from src.features.auto_instrumentation.domain.mappers import ProviderMapper
from src.features.spans.types import FinishReason

def test_map_openai_response():
    mock_response = MagicMock()
    mock_response.model = "gpt-4o"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    
    mock_choice = MagicMock()
    mock_choice.finish_reason = "stop"
    mock_choice.message.content = "Hello"
    mock_response.choices = [mock_choice]
    
    result = ProviderMapper.map_openai_response(mock_response)
    
    assert result["model"] == "gpt-4o"
    assert result["provider"] == "openai"
    assert result["prompt_tokens"] == 10
    assert result["completion_tokens"] == 20
    assert result["finish_reason"] == FinishReason.STOP
    assert result["response_content"] == "Hello"

def test_map_openai_response_missing_usage():
    mock_response = MagicMock()
    mock_response.model = "gpt-4o"
    mock_response.usage = None
    mock_response.choices = []
    
    result = ProviderMapper.map_openai_response(mock_response)
    assert result["prompt_tokens"] == 1
    assert result["completion_tokens"] == 0
    assert result["finish_reason"] == FinishReason.UNSPECIFIED

def test_map_openai_response_various_finish_reasons():
    reasons = [
        ("stop", FinishReason.STOP),
        ("length", FinishReason.LENGTH),
        ("content_filter", FinishReason.CONTENT_FILTER),
        ("tool_calls", FinishReason.TOOL_CALLS),
        ("unspecified", FinishReason.UNSPECIFIED),
    ]
    for original, expected in reasons:
        mock_response = MagicMock()
        mock_response.model = "gpt-4"
        mock_choice = MagicMock()
        mock_choice.finish_reason = original
        mock_response.choices = [mock_choice]
        result = ProviderMapper.map_openai_response(mock_response)
        assert result["finish_reason"] == expected

def test_map_anthropic_response():
    mock_response = MagicMock()
    mock_response.model = "claude-3-5-sonnet"
    mock_response.usage.input_tokens = 15
    mock_response.usage.output_tokens = 25
    mock_response.stop_reason = "end_turn"
    
    mock_content = MagicMock()
    mock_content.text = "Hi"
    mock_response.content = [mock_content]
    
    result = ProviderMapper.map_anthropic_response(mock_response)
    
    assert result["model"] == "claude-3-5-sonnet"
    assert result["provider"] == "anthropic"
    assert result["prompt_tokens"] == 15
    assert result["completion_tokens"] == 25
    assert result["finish_reason"] == FinishReason.STOP
    assert result["response_content"] == "Hi"

def test_map_anthropic_response_missing_usage():
    mock_response = MagicMock()
    mock_response.model = "claude-3"
    mock_response.usage = None
    mock_response.content = []
    
    result = ProviderMapper.map_anthropic_response(mock_response)
    assert result["prompt_tokens"] == 1
    assert result["completion_tokens"] == 0

def test_map_anthropic_response_various_stop_reasons():
    reasons = [
        ("end_turn", FinishReason.STOP),
        ("max_tokens", FinishReason.LENGTH),
        ("stop_sequence", FinishReason.STOP),
        ("tool_use", FinishReason.TOOL_CALLS),
        ("unknown", FinishReason.UNSPECIFIED),
    ]
    for original, expected in reasons:
        mock_response = MagicMock()
        mock_response.model = "claude-3"
        mock_response.stop_reason = original
        mock_response.content = []
        result = ProviderMapper.map_anthropic_response(mock_response)
        assert result["finish_reason"] == expected

def test_map_anthropic_empty_content():
    mock_response = MagicMock()
    mock_response.model = "claude-3"
    mock_response.content = None
    result = ProviderMapper.map_anthropic_response(mock_response)
    assert result["response_content"] == ""

def test_map_openai_multiple_choices():
    mock_response = MagicMock()
    mock_response.model = "gpt-4"
    mock_choice_1 = MagicMock()
    mock_choice_1.finish_reason = "stop"
    mock_choice_1.message.content = "First"
    mock_choice_2 = MagicMock()
    mock_choice_2.finish_reason = "length"
    mock_choice_2.message.content = "Second"
    mock_response.choices = [mock_choice_1, mock_choice_2]
    
    result = ProviderMapper.map_openai_response(mock_response)
    assert result["response_content"] == "First"
    assert result["finish_reason"] == FinishReason.STOP

def test_map_openai_no_choices():
    mock_response = MagicMock()
    mock_response.model = "gpt-4"
    mock_response.choices = []
    result = ProviderMapper.map_openai_response(mock_response)
    assert result["finish_reason"] == FinishReason.UNSPECIFIED
    assert result["response_content"] is None
