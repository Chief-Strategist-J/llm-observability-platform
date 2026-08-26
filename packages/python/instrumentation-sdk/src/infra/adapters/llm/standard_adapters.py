from typing import Any, Dict, Optional
from src.features.spans.types import FinishReason
from .port import LlmProviderAdapterPort

class OpenAIAdapter(LlmProviderAdapterPort):
    def provider_name(self) -> str:
        return "openai"

    def map_response(self, response: Any, model: Optional[str] = None) -> Dict[str, Any]:
        usage = getattr(response, "usage", None)
        choices = getattr(response, "choices", [])
        
        finish_reason = FinishReason.UNSPECIFIED
        if choices:
            reason = getattr(choices[0], "finish_reason", None)
            if reason == "stop":
                finish_reason = FinishReason.STOP
            elif reason == "length":
                finish_reason = FinishReason.LENGTH
            elif reason == "content_filter":
                finish_reason = FinishReason.CONTENT_FILTER
            elif reason == "tool_calls":
                finish_reason = FinishReason.TOOL_CALLS

        content = choices[0].message.content if choices and hasattr(choices[0], "message") and hasattr(choices[0].message, "content") else None

        return {
            "model": model or getattr(response, "model", "gpt-4o"),
            "provider": self.provider_name(),
            "prompt_tokens": getattr(usage, "prompt_tokens", 1) if usage else 1,
            "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
            "finish_reason": finish_reason,
            "response_content": content
        }

class AnthropicAdapter(LlmProviderAdapterPort):
    def provider_name(self) -> str:
        return "anthropic"

    def map_response(self, response: Any, model: Optional[str] = None) -> Dict[str, Any]:
        usage = getattr(response, "usage", None)
        
        finish_reason = FinishReason.UNSPECIFIED
        stop_reason = getattr(response, "stop_reason", None)
        if stop_reason in ["end_turn", "stop_sequence"]:
            finish_reason = FinishReason.STOP
        elif stop_reason == "max_tokens":
            finish_reason = FinishReason.LENGTH
        elif stop_reason == "tool_use":
            finish_reason = FinishReason.TOOL_CALLS

        content = ""
        if hasattr(response, "content") and response.content:
            content = response.content[0].text if hasattr(response.content[0], "text") else ""

        return {
            "model": model or getattr(response, "model", "claude-3-5-sonnet"),
            "provider": self.provider_name(),
            "prompt_tokens": getattr(usage, "input_tokens", 1) if usage else 1,
            "completion_tokens": getattr(usage, "output_tokens", 0) if usage else 0,
            "finish_reason": finish_reason,
            "response_content": content
        }
