from __future__ import annotations

from core.domain.rules import TOXICITY_THRESHOLD, determine_flag, is_flagged


def test_is_flagged_above_threshold():
    assert is_flagged(0.51) is True


def test_is_flagged_on_threshold():
    assert is_flagged(0.50) is False


def test_is_flagged_below_threshold():
    assert is_flagged(0.49) is False


def test_determine_flag_above_threshold():
    assert determine_flag(0.51) == "TOXIC_RESPONSE"


def test_determine_flag_on_threshold():
    assert determine_flag(0.50) is None


def test_determine_flag_below_threshold():
    assert determine_flag(0.49) is None
