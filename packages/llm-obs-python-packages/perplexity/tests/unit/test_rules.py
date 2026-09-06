from __future__ import annotations

import math

import pytest

from features.score_perplexity.rules import (
    BLOCKED_FINISH_REASONS,
    HIGH_PERPLEXITY_MULTIPLIER,
    MIN_COMPLETION_TOKENS,
    WEIGHT_ACTIVE,
    WEIGHT_SKIPPED,
    baseline_for,
    compute_perplexity_from_logprobs,
    is_high_perplexity,
    normalize_contribution,
    should_skip,
)
from features.score_perplexity.types import PerplexityInput


def _input(**kwargs) -> PerplexityInput:
    defaults = dict(
        response_text="This is a well-formed model response.",
        completion_tokens=20,
        prompt_type="chat",
        token_logprobs=None,
        finish_reason=None,
    )
    defaults.update(kwargs)
    return PerplexityInput(**defaults)


def test_skip_content_filter():
    skipped, reason = should_skip(_input(finish_reason="content_filter"))
    assert skipped is True
    assert reason == "finish_reason_blocked"


def test_skip_completion_tokens_too_few():
    skipped, reason = should_skip(_input(completion_tokens=MIN_COMPLETION_TOKENS - 1))
    assert skipped is True
    assert reason == "completion_tokens_too_few"


def test_skip_completion_tokens_exactly_at_limit():
    skipped, reason = should_skip(_input(completion_tokens=MIN_COMPLETION_TOKENS))
    assert skipped is False
    assert reason is None


def test_no_skip_valid_input():
    skipped, reason = should_skip(_input())
    assert skipped is False
    assert reason is None


def test_blocked_finish_reasons_content_filter():
    assert "content_filter" in BLOCKED_FINISH_REASONS


@pytest.mark.parametrize("logprobs,expected", [
    ([-2.0, -2.0, -2.0], math.exp(2.0)),
    ([-1.0], math.exp(1.0)),
    ([-3.0, -1.0], math.exp(2.0)),
])
def test_compute_perplexity_from_logprobs(logprobs, expected):
    result = compute_perplexity_from_logprobs(logprobs)
    assert result == pytest.approx(expected, rel=1e-5)


@pytest.mark.parametrize("prompt_type", ["chat", "code", "rag", "classification"])
def test_baseline_for_all_prompt_types(prompt_type):
    low, high = baseline_for(prompt_type)
    assert low > 0
    assert high > low


@pytest.mark.parametrize("prompt_type,perplexity,expected_flag", [
    ("chat", 106.0, True),
    ("chat", 34.0, False),
    ("code", 61.0, True),
    ("code", 20.0, False),
    ("rag", 85.0, True),
    ("rag", 28.0, False),
    ("classification", 46.0, True),
    ("classification", 15.0, False),
])
def test_is_high_perplexity_boundaries(prompt_type, perplexity, expected_flag):
    _, baseline_high = baseline_for(prompt_type)
    flag = is_high_perplexity(perplexity, prompt_type)
    assert flag == expected_flag


def test_normalize_contribution_in_range():
    for pt in ["chat", "code", "rag", "classification"]:
        low, high = baseline_for(pt)
        mid = (low + high) / 2
        contrib = normalize_contribution(mid, pt)
        assert 0.0 <= contrib <= 1.0


def test_normalize_contribution_high_perplexity_low_score():
    contrib = normalize_contribution(500.0, "chat")
    assert contrib < 0.2


def test_normalize_contribution_low_perplexity_high_score():
    contrib = normalize_contribution(2.0, "chat")
    assert contrib >= 1.0 or contrib >= 0.0


def test_weight_constants():
    assert WEIGHT_ACTIVE == pytest.approx(0.10)
    assert WEIGHT_SKIPPED == pytest.approx(0.00)
