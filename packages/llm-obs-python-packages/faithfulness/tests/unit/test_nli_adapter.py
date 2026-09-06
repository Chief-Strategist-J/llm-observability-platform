from __future__ import annotations

import pytest

from infra.adapters.nli.deberta_nli_adapter import DeBertaNliAdapter
from features.score_faithfulness.rules import TEMPERATURE, NLI_BATCH_SIZE


class FakeTokenizer:
    def __call__(self, premises, hypotheses, **kwargs):
        return {"input_ids": [[1, 2, 3]] * len(premises)}


class FakeOutput:
    def __init__(self, logits):
        self.logits = logits


class FakeModel:
    def __init__(self):
        import types
        self.config = types.SimpleNamespace(
            id2label={0: "contradiction", 1: "neutral", 2: "entailment"}
        )

    def eval(self):
        return self

    def __call__(self, **kwargs):
        import torch
        n = len(kwargs["input_ids"])
        logits = torch.zeros(n, 3)
        logits[:, 2] = 2.0
        return FakeOutput(logits)


def _adapter_with_fakes() -> DeBertaNliAdapter:
    adapter = DeBertaNliAdapter.__new__(DeBertaNliAdapter)
    adapter._model_id = "test/fake-model"
    adapter.__dict__["_tokenizer"] = FakeTokenizer()
    adapter.__dict__["_model"] = FakeModel()
    return adapter


def test_model_id_property():
    adapter = _adapter_with_fakes()
    assert adapter.model_id == "test/fake-model"


def test_score_pairs_returns_correct_length():
    adapter = _adapter_with_fakes()
    pairs = [("premise one", "hypothesis one"), ("premise two", "hypothesis two")]
    result = adapter.score_pairs(pairs)
    assert len(result) == 2


def test_score_pairs_each_is_triple():
    adapter = _adapter_with_fakes()
    pairs = [("premise", "hypothesis")]
    result = adapter.score_pairs(pairs)
    assert len(result[0]) == 3


def test_score_pairs_probs_sum_to_one():
    adapter = _adapter_with_fakes()
    pairs = [("The sky is blue.", "It is daytime.")]
    result = adapter.score_pairs(pairs)
    total = sum(result[0])
    assert pytest.approx(1.0, abs=1e-4) == total


def test_score_pairs_with_fake_entailment_logit():
    adapter = _adapter_with_fakes()
    pairs = [("premise", "hypothesis")]
    result = adapter.score_pairs(pairs)
    e, n, c = result[0]
    assert e > n
    assert e > c


def test_score_pairs_batching_splits_correctly():
    adapter = _adapter_with_fakes()
    pairs = [("p", "h")] * (NLI_BATCH_SIZE + 1)
    result = adapter.score_pairs(pairs)
    assert len(result) == NLI_BATCH_SIZE + 1


def test_score_pairs_empty_returns_empty():
    adapter = _adapter_with_fakes()
    result = adapter.score_pairs([])
    assert result == []
