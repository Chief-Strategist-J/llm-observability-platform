from __future__ import annotations

import math

import pytest

from features.score_perplexity.service import score_perplexity
from features.score_perplexity.types import PerplexityInput


class FakeLogprobsScorer:
    def __init__(self, result: float | None) -> None:
        self._result = result

    def compute(self, token_logprobs: list[float] | None, response_text: str) -> float | None:
        return self._result


class FakeGpt2Scorer:
    def __init__(self, available: bool = True, result: float | None = 20.0) -> None:
        self._available = available
        self._result = result

    def is_available(self) -> bool:
        return self._available

    def compute(self, response_text: str) -> float | None:
        return self._result


def _valid_input(**kwargs) -> PerplexityInput:
    defaults = dict(
        response_text="The answer is well-formed and coherent.",
        completion_tokens=20,
        prompt_type="chat",
        token_logprobs=None,
        finish_reason=None,
    )
    defaults.update(kwargs)
    return PerplexityInput(**defaults)


def test_skip_completion_tokens_too_few():
    result = score_perplexity(
        input=_valid_input(completion_tokens=5),
        logprobs_scorer=FakeLogprobsScorer(None),
        gpt2_scorer=FakeGpt2Scorer(available=False),
    )
    assert result.skipped is True
    assert result.skip_reason == "completion_tokens_too_few"
    assert result.perplexity is None
    assert result.score is None
    assert result.weight == pytest.approx(0.0)


def test_skip_content_filter():
    result = score_perplexity(
        input=_valid_input(finish_reason="content_filter"),
        logprobs_scorer=FakeLogprobsScorer(None),
        gpt2_scorer=FakeGpt2Scorer(available=False),
    )
    assert result.skipped is True
    assert result.skip_reason == "finish_reason_blocked"
    assert result.weight == pytest.approx(0.0)


def test_skip_scorer_unavailable():
    result = score_perplexity(
        input=_valid_input(),
        logprobs_scorer=FakeLogprobsScorer(None),
        gpt2_scorer=FakeGpt2Scorer(available=False),
    )
    assert result.skipped is True
    assert result.skip_reason == "scorer_unavailable"
    assert result.weight == pytest.approx(0.0)


def test_uses_provider_logprobs_when_available():
    perplexity_val = 20.0
    result = score_perplexity(
        input=_valid_input(token_logprobs=[-math.log(perplexity_val)]),
        logprobs_scorer=FakeLogprobsScorer(perplexity_val),
        gpt2_scorer=FakeGpt2Scorer(available=True, result=999.0),
    )
    assert result.skipped is False
    assert result.scorer_used == "provider_logprobs"
    assert result.perplexity == pytest.approx(perplexity_val)
    assert result.weight == pytest.approx(0.10)


def test_falls_back_to_gpt2_when_logprobs_unavailable():
    result = score_perplexity(
        input=_valid_input(),
        logprobs_scorer=FakeLogprobsScorer(None),
        gpt2_scorer=FakeGpt2Scorer(available=True, result=18.0),
    )
    assert result.skipped is False
    assert result.scorer_used == "gpt2_onnx"
    assert result.perplexity == pytest.approx(18.0)
    assert result.weight == pytest.approx(0.10)


def test_high_perplexity_flag_raised():
    result = score_perplexity(
        input=_valid_input(prompt_type="chat"),
        logprobs_scorer=FakeLogprobsScorer(200.0),
        gpt2_scorer=FakeGpt2Scorer(available=False),
    )
    assert result.high_perplexity_flag is True


def test_high_perplexity_flag_not_raised_for_normal():
    result = score_perplexity(
        input=_valid_input(prompt_type="chat"),
        logprobs_scorer=FakeLogprobsScorer(20.0),
        gpt2_scorer=FakeGpt2Scorer(available=False),
    )
    assert result.high_perplexity_flag is False


def test_score_normalized_to_range():
    result = score_perplexity(
        input=_valid_input(prompt_type="code"),
        logprobs_scorer=FakeLogprobsScorer(12.0),
        gpt2_scorer=FakeGpt2Scorer(available=False),
    )
    assert result.score is not None
    assert 0.0 <= result.score <= 1.0


def test_prompt_type_preserved_in_result():
    result = score_perplexity(
        input=_valid_input(prompt_type="rag"),
        logprobs_scorer=FakeLogprobsScorer(15.0),
        gpt2_scorer=FakeGpt2Scorer(available=False),
    )
    assert result.prompt_type == "rag"


def test_weight_is_zero_when_skipped():
    result = score_perplexity(
        input=_valid_input(completion_tokens=1),
        logprobs_scorer=FakeLogprobsScorer(None),
        gpt2_scorer=FakeGpt2Scorer(available=False),
    )
    assert result.weight == pytest.approx(0.0)


def test_weight_is_0_10_when_not_skipped():
    result = score_perplexity(
        input=_valid_input(),
        logprobs_scorer=FakeLogprobsScorer(25.0),
        gpt2_scorer=FakeGpt2Scorer(available=False),
    )
    assert result.weight == pytest.approx(0.10)


def test_gpt2_result_none_treated_as_unavailable():
    result = score_perplexity(
        input=_valid_input(),
        logprobs_scorer=FakeLogprobsScorer(None),
        gpt2_scorer=FakeGpt2Scorer(available=True, result=None),
    )
    assert result.skipped is True
    assert result.skip_reason == "scorer_unavailable"
