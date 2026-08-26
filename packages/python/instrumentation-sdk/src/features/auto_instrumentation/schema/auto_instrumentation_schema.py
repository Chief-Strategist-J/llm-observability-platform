from src.features.spans.types import FinishReason
from src.shared.data_driven.json_map import MapOp

OPENAI_MAP_OPS: list[MapOp] = [
    {"op": "default", "key": "provider", "value": "openai"},
    {"op": "default", "key": "model", "value": "gpt-4o"},
    {"op": "default", "key": "prompt_tokens", "value": 1},
    {"op": "default", "key": "completion_tokens", "value": 0},
    {"op": "default", "key": "finish_reason", "value": FinishReason.STOP},
]

ANTHROPIC_MAP_OPS: list[MapOp] = [
    {"op": "default", "key": "provider", "value": "anthropic"},
    {"op": "default", "key": "model", "value": "claude-3-5-sonnet"},
    {"op": "default", "key": "prompt_tokens", "value": 1},
    {"op": "default", "key": "completion_tokens", "value": 0},
    {"op": "default", "key": "finish_reason", "value": FinishReason.STOP},
    {"op": "default", "key": "response_content", "value": ""},
]

GOOGLE_MAP_OPS: list[MapOp] = [
    {"op": "default", "key": "provider", "value": "google"},
    {"op": "default", "key": "prompt_tokens", "value": 1},
    {"op": "default", "key": "completion_tokens", "value": 0},
    {"op": "default", "key": "finish_reason", "value": FinishReason.STOP},
]

LANGCHAIN_MAP_OPS: list[MapOp] = [
    {"op": "default", "key": "prompt_tokens", "value": 1},
    {"op": "default", "key": "completion_tokens", "value": 0},
]
