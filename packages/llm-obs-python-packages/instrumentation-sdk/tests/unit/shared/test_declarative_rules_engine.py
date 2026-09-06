import pytest
from src.shared.rules_engine.declarative_evaluator import DeclarativeRulesEngine, DeclarativeRuleSpec, normalize_text
from src.features.spans.types import FinishReason

def test_normalize_text_edge_cases():
    assert normalize_text("STOP") == "stop"
    assert normalize_text("  maxTokens  ") == "max_tokens"
    assert normalize_text("Content-Filter") == "content_filter"
    assert normalize_text("toolCalls") == "tool_calls"
    assert normalize_text("FUNCTION_CALL") == "function_call"

def test_declarative_rules_engine_edge_case_matching():
    specs: list[DeclarativeRuleSpec] = [
        {"id": "stop", "match_type": "contains", "patterns": ["stop", "finish"], "value": FinishReason.STOP, "priority": 10},
        {"id": "length", "match_type": "contains", "patterns": ["max_tokens", "length"], "value": FinishReason.LENGTH, "priority": 20},
    ]
    engine = DeclarativeRulesEngine(specs)

    assert engine.evaluate("STOP") == FinishReason.STOP
    assert engine.evaluate("MAX_TOKENS") == FinishReason.LENGTH
    assert engine.evaluate("maxTokens") == FinishReason.LENGTH
    assert engine.evaluate("  Finish_Sequence  ") == FinishReason.STOP
    assert engine.evaluate("unknown_reason", default=FinishReason.UNSPECIFIED) == FinishReason.UNSPECIFIED
