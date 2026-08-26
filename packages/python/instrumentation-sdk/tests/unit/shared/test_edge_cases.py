import pytest
from enum import Enum
from src.shared.rules_engine.declarative_evaluator import DeclarativeRulesEngine, DeclarativeRuleSpec, normalize_text
from src.shared.data_driven.json_map import map_json, MapOp
from src.features.spans.types import FinishReason

class SampleEnum(Enum):
    STOP_VAL = "stop_sequence"

def test_enum_normalization():
    assert normalize_text(SampleEnum.STOP_VAL) == "stop_sequence"

def test_nested_path_json_mapping():
    data = {
        "choices": [
            {"message": {"content": "Hello world"}}
        ]
    }
    ops: list[MapOp] = [
        {"op": "rename", "path": "choices.0.message.content", "to_key": "response_content"},
        {"op": "default", "key": "model", "value": "gpt-4o"}
    ]
    result = map_json(data, ops)
    assert result["response_content"] == "Hello world"
    assert result["model"] == "gpt-4o"
