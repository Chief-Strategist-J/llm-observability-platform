from __future__ import annotations


class GenAIAttributes:
    SYSTEM = "gen_ai.system"
    REQUEST_MODEL = "gen_ai.request.model"
    RESPONSE_MODEL = "gen_ai.response.model"
    USAGE_PROMPT_TOKENS = "gen_ai.usage.prompt_tokens"
    USAGE_COMPLETION_TOKENS = "gen_ai.usage.completion_tokens"
    LATENCY_TTFT = "gen_ai.latency.ttft_ms"
    LATENCY_TOTAL = "gen_ai.latency.total_ms"
