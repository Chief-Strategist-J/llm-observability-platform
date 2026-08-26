from typing import Any, Dict, Optional
from src.features.spans.types import FinishReason
from src.shared.rules_engine.declarative_evaluator import DeclarativeRulesEngine
from ..ports.adapter_port import LlmProviderAdapterPort
from ..rules.rules import GOOGLE_FINISH_RULE_SPECS

google_rules_engine = DeclarativeRulesEngine(GOOGLE_FINISH_RULE_SPECS)

class GoogleGeminiAdapter(LlmProviderAdapterPort):
    def provider_name(self) -> str:
        return "google"

    def map_response(self, response: Any, model: Optional[str] = None) -> Dict[str, Any]:
        usage = getattr(response, "usage_metadata", None)
        candidates = getattr(response, "candidates", [])
        
        raw_reason = candidates[0].finish_reason if (candidates and hasattr(candidates[0], "finish_reason")) else ""
        finish_reason = google_rules_engine.evaluate(raw_reason, default=FinishReason.UNSPECIFIED)

        prompt_tokens = getattr(usage, "prompt_token_count", 1) if usage else 1
        completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
        text = getattr(response, "text", "")

        return {
            "model": model or getattr(response, "model_version", "gemini-1.5-pro"),
            "provider": self.provider_name(),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "finish_reason": finish_reason,
            "response_content": text,
        }
