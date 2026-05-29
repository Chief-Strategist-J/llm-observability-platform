from __future__ import annotations

import pytest

from infra.adapters.detoxify_onnx_adapter import DetoxifyOnnxAdapter

class FakeTokenizer:
    cls_token_id = 101
    sep_token_id = 102

    def encode(self, text: str, add_special_tokens: bool) -> list[int]:
        return [1, 2, 3]

class FakeOutput:
    def __init__(self, logits) -> None:
        self.logits = logits

class FakeModel:
    def __init__(self) -> None:
        import types
        self.config = types.SimpleNamespace(
            id2label={
                0: "toxicity",
                1: "severe_toxicity",
                2: "obscene",
                3: "threat",
                4: "insult",
                5: "identity_hate",
            }
        )

    def __call__(self, **kwargs):
        import torch
        return FakeOutput(torch.tensor([[0.0, 1.0, 2.0, 3.0, 4.0, 5.0]]))

def _adapter_with_fakes() -> DetoxifyOnnxAdapter:
    adapter = DetoxifyOnnxAdapter.__new__(DetoxifyOnnxAdapter)
    adapter._model_id = "test/fake-model"
    adapter.__dict__["_tokenizer"] = FakeTokenizer()
    adapter.__dict__["_model"] = FakeModel()
    return adapter

def test_model_id_property():
    adapter = _adapter_with_fakes()
    assert adapter.model_id == "test/fake-model"

def test_tokenize():
    adapter = _adapter_with_fakes()
    assert adapter.tokenize("test") == [1, 2, 3]

def test_score_token_ids():
    adapter = _adapter_with_fakes()
    scores = adapter.score_token_ids([1, 2, 3])
    assert scores.toxicity > 0.0
    assert scores.severe_toxicity > 0.0
