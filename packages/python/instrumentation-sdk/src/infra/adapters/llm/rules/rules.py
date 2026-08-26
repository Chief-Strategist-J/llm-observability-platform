from src.features.spans.types import FinishReason
from src.shared.rules_engine.declarative_evaluator import DeclarativeRuleSpec

FINISH_REASON_RULE_SPECS: list[DeclarativeRuleSpec] = [
    {
        "id": "stop_rule",
        "match_type": "contains",
        "patterns": ["stop", "end_turn", "stop_sequence", "completed", "finish"],
        "value": FinishReason.STOP,
        "priority": 40,
    },
    {
        "id": "length_rule",
        "match_type": "contains",
        "patterns": ["max_tokens", "length", "token_limit", "maxTokens"],
        "value": FinishReason.LENGTH,
        "priority": 30,
    },
    {
        "id": "content_filter_rule",
        "match_type": "contains",
        "patterns": ["safety", "block", "content_filter", "contentFilter", "flagged"],
        "value": FinishReason.CONTENT_FILTER,
        "priority": 20,
    },
    {
        "id": "tool_calls_rule",
        "match_type": "contains",
        "patterns": ["tool_calls", "tool_use", "toolCalls", "function_call", "functionCall"],
        "value": FinishReason.TOOL_CALLS,
        "priority": 10,
    },
]

OPENAI_FINISH_RULE_SPECS = FINISH_REASON_RULE_SPECS
ANTHROPIC_FINISH_RULE_SPECS = FINISH_REASON_RULE_SPECS
GOOGLE_FINISH_RULE_SPECS = FINISH_REASON_RULE_SPECS
