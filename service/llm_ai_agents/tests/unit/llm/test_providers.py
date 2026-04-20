import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage


def _make_config(model_id: str = "gpt-4o-mini") -> dict:
    return {"model": {"provider": "openai", "id": model_id, "parameters": {"temperature": 0.7, "max_tokens": 512}}}


@pytest.fixture
def mock_chat_openai():
    mock = MagicMock()
    mock.invoke.return_value = AIMessage(content="openai response")
    mock.stream.return_value = iter([AIMessage(content="hello"), AIMessage(content=" world")])
    return mock


def test_openai_generate_returns_llm_content(mock_chat_openai):
    with patch("services.llm.providers.openai.ChatOpenAI", return_value=mock_chat_openai):
        from services.llm.providers.openai import OpenAIProvider
        provider = OpenAIProvider(_make_config())
        result = provider.generate("test prompt")
        assert result == "openai response"
        mock_chat_openai.invoke.assert_called_once()


def test_openai_stream_generate_yields_tokens(mock_chat_openai):
    with patch("services.llm.providers.openai.ChatOpenAI", return_value=mock_chat_openai):
        from services.llm.providers.openai import OpenAIProvider
        provider = OpenAIProvider(_make_config())
        tokens = list(provider.stream_generate("test prompt"))
        assert tokens == ["hello", " world"]


def test_openai_uses_correct_model_id(mock_chat_openai):
    with patch("services.llm.providers.openai.ChatOpenAI") as MockCls:
        MockCls.return_value = mock_chat_openai
        from services.llm.providers.openai import OpenAIProvider
        OpenAIProvider(_make_config("gpt-4o"))
        call_kwargs = MockCls.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o"
