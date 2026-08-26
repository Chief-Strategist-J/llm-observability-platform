from typing import Any, Dict, Optional
from ...spans.types import FinishReason
from src.infra.adapters.llm.registry import LlmProviderRegistry

class ProviderMapper:
    @staticmethod
    def map_openai_response(response: Any) -> Dict[str, Any]:
        adapter = LlmProviderRegistry.get("openai")
        if adapter:
            return adapter.map_response(response)

        usage = getattr(response, "usage", None)
        choices = getattr(response, "choices", [])
        return {
            "model": getattr(response, "model", "gpt-4o"),
            "provider": "openai",
            "prompt_tokens": usage.prompt_tokens if usage else 1,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "finish_reason": FinishReason.STOP if choices else FinishReason.UNSPECIFIED,
            "response_content": choices[0].message.content if choices and hasattr(choices[0].message, "content") else None
        }

    @staticmethod
    def map_anthropic_response(response: Any) -> Dict[str, Any]:
        adapter = LlmProviderRegistry.get("anthropic")
        if adapter:
            return adapter.map_response(response)

        usage = getattr(response, "usage", None)
        return {
            "model": getattr(response, "model", "claude-3-5-sonnet"),
            "provider": "anthropic",
            "prompt_tokens": usage.input_tokens if usage else 1,
            "completion_tokens": usage.output_tokens if usage else 0,
            "finish_reason": FinishReason.STOP,
            "response_content": ""
        }

    @staticmethod
    def map_google_response(response: Any, model: Optional[str] = None) -> Dict[str, Any]:
        adapter = LlmProviderRegistry.get("google")
        if adapter:
            return adapter.map_response(response, model=model)
        return {
            "model": model or "gemini-1.5-pro",
            "provider": "google",
            "prompt_tokens": 1,
            "completion_tokens": 0,
            "finish_reason": FinishReason.STOP,
            "response_content": getattr(response, "text", "")
        }

    @staticmethod
    def map_langchain_response(response: Any, model: str, provider: str) -> Dict[str, Any]:
        usage = getattr(response, "usage_metadata", {})
        if not usage:
            usage = {}
            
        return {
            "model": model,
            "provider": f"langchain:{provider}",
            "prompt_tokens": usage.get("input_tokens", 1),
            "completion_tokens": usage.get("output_tokens", 0),
            "finish_reason": FinishReason.STOP if hasattr(response, "content") else FinishReason.UNSPECIFIED,
            "response_content": getattr(response, "content", "")
        }
