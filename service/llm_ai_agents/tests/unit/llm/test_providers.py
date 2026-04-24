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


def _make_cloudflare_config(model_id: str = "@cf/meta/llama-3.1-8b-instruct") -> dict:
    return {"model": {"provider": "cloudflare", "id": model_id, "parameters": {"temperature": 0.3, "max_tokens": 256}}}


def test_cloudflare_uses_workers_ai_endpoint(mock_chat_openai):
    with patch("services.llm.providers.cloudflare.ChatOpenAI") as MockCls, \
         patch.dict("os.environ", {"CLOUDFLARE_ACCOUNT_ID": "acct123", "CLOUDFLARE_API_TOKEN": "token123"}, clear=False):
        MockCls.return_value = mock_chat_openai
        from services.llm.providers.cloudflare import CloudflareWorkersAIProvider
        CloudflareWorkersAIProvider(_make_cloudflare_config())
        call_kwargs = MockCls.call_args.kwargs
        assert call_kwargs["api_key"] == "token123"
        assert call_kwargs["base_url"] == "https://api.cloudflare.com/client/v4/accounts/acct123/ai/v1"


def test_cloudflare_allows_base_url_override(mock_chat_openai):
    with patch("services.llm.providers.cloudflare.ChatOpenAI") as MockCls, \
         patch.dict("os.environ", {
             "CLOUDFLARE_ACCOUNT_ID": "acct123",
             "CLOUDFLARE_API_TOKEN": "token123",
             "CLOUDFLARE_BASE_URL": "https://custom.example/v1"
         }, clear=False):
        MockCls.return_value = mock_chat_openai
        from services.llm.providers.cloudflare import CloudflareWorkersAIProvider
        CloudflareWorkersAIProvider(_make_cloudflare_config())
        call_kwargs = MockCls.call_args.kwargs
        assert call_kwargs["base_url"] == "https://custom.example/v1"



def test_cloudflare_requires_api_token(mock_chat_openai):
    with patch.dict("os.environ", {"CLOUDFLARE_ACCOUNT_ID": "acct123", "CLOUDFLARE_API_TOKEN": ""}, clear=False):
        from services.llm.providers.cloudflare import CloudflareWorkersAIProvider
        with pytest.raises(ValueError) as exc_info:
            CloudflareWorkersAIProvider(_make_cloudflare_config())
        assert "CLOUDFLARE_API_TOKEN" in str(exc_info.value)


def test_cloudflare_requires_account_id_if_no_override(mock_chat_openai):
    with patch.dict("os.environ", {"CLOUDFLARE_ACCOUNT_ID": "", "CLOUDFLARE_API_TOKEN": "token123", "CLOUDFLARE_BASE_URL": ""}, clear=False):
        from services.llm.providers.cloudflare import CloudflareWorkersAIProvider
        with pytest.raises(ValueError) as exc_info:
            CloudflareWorkersAIProvider(_make_cloudflare_config())
        assert "CLOUDFLARE_ACCOUNT_ID" in str(exc_info.value)


def test_cloudflare_trims_trailing_slash_on_base_url(mock_chat_openai):
    with patch("services.llm.providers.cloudflare.ChatOpenAI") as MockCls, \
         patch.dict("os.environ", {
             "CLOUDFLARE_API_TOKEN": "token123",
             "CLOUDFLARE_BASE_URL": "https://custom.example/v1/"
         }, clear=False):
        MockCls.return_value = mock_chat_openai
        from services.llm.providers.cloudflare import CloudflareWorkersAIProvider
        CloudflareWorkersAIProvider(_make_cloudflare_config())
        call_kwargs = MockCls.call_args.kwargs
        assert call_kwargs["base_url"] == "https://custom.example/v1"
