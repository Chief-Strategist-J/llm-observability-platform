import pytest
from unittest.mock import patch, MagicMock
from services.llm.factory import LLMFactory
from services.llm.base.llm import BaseLLM
from services.shared.exceptions import ProviderNotFoundError


def _config(provider: str, model_id: str = "test-model") -> dict:
    return {"model": {"provider": provider, "id": model_id}}


def test_factory_raises_for_unknown_provider():
    with pytest.raises(ProviderNotFoundError) as exc_info:
        LLMFactory.create(_config("does-not-exist"))
    assert "does-not-exist" in str(exc_info.value)


@pytest.mark.parametrize("provider", [
    "openai", "anthropic", "gemini", "grok", "mistral", "huggingface", "cloudflare"
])
def test_factory_instantiates_correct_provider(provider):
    sentinel = MagicMock(spec=BaseLLM)
    mock_cls = MagicMock(return_value=sentinel)
    
    # Patch the registry dictionary directly in the factory module
    with patch.dict("services.llm.factory.PROVIDER_REGISTRY", {provider: mock_cls}, clear=False):
        result = LLMFactory.create(_config(provider))
        mock_cls.assert_called_once()
        assert result is sentinel


def test_factory_passes_full_config_to_provider():
    config = {"model": {"provider": "openai", "id": "gpt-4", "parameters": {"temp": 0.5}}}
    sentinel = MagicMock(spec=BaseLLM)
    mock_cls = MagicMock(return_value=sentinel)
    
    with patch.dict("services.llm.factory.PROVIDER_REGISTRY", {"openai": mock_cls}, clear=False):
        LLMFactory.create(config)
        mock_cls.assert_called_once_with(config)
