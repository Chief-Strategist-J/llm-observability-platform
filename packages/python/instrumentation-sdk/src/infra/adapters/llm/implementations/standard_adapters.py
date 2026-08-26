from typing import Any, Dict, Optional
from src.features.spans.types import FinishReason
from src.shared.rules_engine.declarative_evaluator import DeclarativeRulesEngine
from ..ports.adapter_port import LlmProviderAdapterPort
from ..rules.rules import OPENAI_FINISH_RULE_SPECS, ANTHROPIC_FINISH_RULE_SPECS

openai_rules_engine = DeclarativeRulesEngine(OPENAI_FINISH_RULE_SPECS)
anthropic_rules_engine = DeclarativeRulesEngine(ANTHROPIC_FINISH_RULE_SPECS)

class OpenAIAdapter(LlmProviderAdapterPort):
    def provider_name(self) -> str:
        return "openai"

    def map_response(self, response: Any, model: Optional[str] = None) -> Dict[str, Any]:
        usage = getattr(response, "usage", None)
        choices = getattr(response, "choices", [])
        
        reason = getattr(choices[0], "finish_reason", None) if choices else None
        finish_reason = openai_rules_engine.evaluate(reason, default=FinishReason.UNSPECIFIED)
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
        stop_reason = getattr(response, "stop_reason", None)
        finish_reason = anthropic_rules_engine.evaluate(stop_reason, default=FinishReason.UNSPECIFIED)

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
