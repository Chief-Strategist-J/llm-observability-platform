from typing import Any, Dict, Optional
from ...spans.types import FinishReason

class ProviderMapper:
    @staticmethod
    def map_openai_response(response: Any) -> Dict[str, Any]:
        usage = getattr(response, "usage", None)
        choices = getattr(response, "choices", [])
        
        finish_reason = FinishReason.UNSPECIFIED
        if choices:
            reason = choices[0].finish_reason
            if reason == "stop":
                finish_reason = FinishReason.STOP
            elif reason == "length":
                finish_reason = FinishReason.LENGTH
            elif reason == "content_filter":
                finish_reason = FinishReason.CONTENT_FILTER
            elif reason == "tool_calls":
                finish_reason = FinishReason.TOOL_CALLS

        return {
            "model": response.model,
            "provider": "openai",
            "prompt_tokens": usage.prompt_tokens if usage else 1,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "finish_reason": finish_reason,
            "response_content": choices[0].message.content if choices and hasattr(choices[0].message, "content") else None
        }

    @staticmethod
    def map_anthropic_response(response: Any) -> Dict[str, Any]:
        usage = getattr(response, "usage", None)
        
        finish_reason = FinishReason.UNSPECIFIED
        stop_reason = getattr(response, "stop_reason", None)
        if stop_reason == "end_turn":
            finish_reason = FinishReason.STOP
        elif stop_reason == "max_tokens":
            finish_reason = FinishReason.LENGTH
        elif stop_reason == "stop_sequence":
            finish_reason = FinishReason.STOP
        elif stop_reason == "tool_use":
            finish_reason = FinishReason.TOOL_CALLS

        content = ""
        if hasattr(response, "content") and response.content:
            content = response.content[0].text if hasattr(response.content[0], "text") else ""

        return {
            "model": response.model,
            "provider": "anthropic",
            "prompt_tokens": usage.input_tokens if usage else 1,
            "completion_tokens": usage.output_tokens if usage else 0,
            "finish_reason": finish_reason,
            "response_content": content
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
