from typing import Any, Dict, Optional
from src.features.spans.types import FinishReason
from src.infra.adapters.llm.registry import LlmProviderRegistry
from src.shared.data_driven.json_map import map_json
from ..schema.auto_instrumentation_schema import (
    OPENAI_MAP_OPS,
    ANTHROPIC_MAP_OPS,
    GOOGLE_MAP_OPS,
    LANGCHAIN_MAP_OPS,
)

class ProviderMapper:
    @classmethod
    def _dispatch_provider(cls, provider_name: str, response: Any, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
        adapter = LlmProviderRegistry.get(provider_name)
        return adapter.map_response(response, model=model) if adapter else None

    @classmethod
    def map_openai_response(cls, response: Any) -> Dict[str, Any]:
        mapped = cls._dispatch_provider("openai", response)
        usage = getattr(response, "usage", None)
        choices = getattr(response, "choices", [])
        raw = {
            "model": getattr(response, "model", None),
            "prompt_tokens": usage.prompt_tokens if usage else None,
            "completion_tokens": usage.completion_tokens if usage else None,
            "finish_reason": FinishReason.STOP if choices else FinishReason.UNSPECIFIED,
            "response_content": choices[0].message.content if choices and hasattr(choices[0].message, "content") else None
        }
        return mapped or map_json(raw, OPENAI_MAP_OPS)

    @classmethod
    def map_anthropic_response(cls, response: Any) -> Dict[str, Any]:
        mapped = cls._dispatch_provider("anthropic", response)
        usage = getattr(response, "usage", None)
        raw = {
            "model": getattr(response, "model", None),
            "prompt_tokens": usage.input_tokens if usage else None,
            "completion_tokens": usage.output_tokens if usage else None,
        }
        return mapped or map_json(raw, ANTHROPIC_MAP_OPS)

    @classmethod
    def map_google_response(cls, response: Any, model: Optional[str] = None) -> Dict[str, Any]:
        mapped = cls._dispatch_provider("google", response, model=model)
        raw = {
            "model": model,
            "response_content": getattr(response, "text", "")
        }
        return mapped or map_json(raw, GOOGLE_MAP_OPS)

    @staticmethod
    def map_langchain_response(response: Any, model: str, provider: str) -> Dict[str, Any]:
        usage = getattr(response, "usage_metadata", {}) or {}
        raw = {
            "model": model,
            "provider": f"langchain:{provider}",
            "prompt_tokens": usage.get("input_tokens", 1),
            "completion_tokens": usage.get("output_tokens", 0),
            "finish_reason": FinishReason.STOP if hasattr(response, "content") else FinishReason.UNSPECIFIED,
            "response_content": getattr(response, "content", "")
        }
        return map_json(raw, LANGCHAIN_MAP_OPS)
