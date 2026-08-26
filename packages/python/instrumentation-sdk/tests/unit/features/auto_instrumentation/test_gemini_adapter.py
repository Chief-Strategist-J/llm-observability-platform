import pytest
from src.infra.adapters.llm.registry import LlmProviderRegistry
from src.features.auto_instrumentation.domain.mappers import ProviderMapper
from src.features.spans.types import FinishReason

class MockGeminiResponse:
    def __init__(self, text="Hello from Gemini", prompt_tokens=12, completion_tokens=24, finish_reason="STOP"):
        self.text = text
        self.model_version = "gemini-1.5-flash"
        self.usage_metadata = type("Usage", (), {
            "prompt_token_count": prompt_tokens,
            "candidates_token_count": completion_tokens
        })()
        self.candidates = [
            type("Candidate", (), {"finish_reason": finish_reason})()
        ]

def test_google_gemini_adapter_direct():
    adapter = LlmProviderRegistry.get("google")
    assert adapter is not None
    assert adapter.provider_name() == "google"

    mock_resp = MockGeminiResponse()
    mapped = adapter.map_response(mock_resp)

    assert mapped["provider"] == "google"
    assert mapped["model"] == "gemini-1.5-flash"
    assert mapped["prompt_tokens"] == 12
    assert mapped["completion_tokens"] == 24
    assert mapped["finish_reason"] == FinishReason.STOP
    assert mapped["response_content"] == "Hello from Gemini"

def test_provider_mapper_google_integration():
    mock_resp = MockGeminiResponse()
    mapped = ProviderMapper.map_google_response(mock_resp, model="gemini-1.5-pro")

    assert mapped["provider"] == "google"
    assert mapped["model"] == "gemini-1.5-pro"
    assert mapped["prompt_tokens"] == 12
    assert mapped["completion_tokens"] == 24
