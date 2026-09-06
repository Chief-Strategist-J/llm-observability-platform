from __future__ import annotations
from handlers.span_quality.baseline_logic import update_baseline_ewma, should_alert_degradation


# ── F-Q-07 EWMA tests ──────────────────────────────────────────────────────

def test_ewma_cold_start_returns_new_score():
    result = update_baseline_ewma(old_mean=None, new_score=0.85, window_count=1)
    assert result == 0.85


def test_ewma_updates_correctly():
    old = 0.80
    result = update_baseline_ewma(old_mean=old, new_score=0.90, window_count=10)
    # n=10: new = (0.80 * 9 + 0.90) / 10 = 0.81
    assert abs(result - 0.81) < 1e-9


def test_ewma_caps_at_max_window():
    # window_count > max_window should still produce valid float
    result = update_baseline_ewma(old_mean=0.75, new_score=0.95, window_count=999999, max_window=10080)
    assert 0.0 < result < 1.0


# ── F-Q-08 degradation alert tests ────────────────────────────────────────

def test_no_alert_when_null_window_avg():
    assert not should_alert_degradation(None, 0.8, sample_count=25)


def test_no_alert_when_null_baseline():
    assert not should_alert_degradation(0.6, None, sample_count=25)


def test_no_alert_below_min_samples():
    assert not should_alert_degradation(0.6, 0.8, sample_count=5)


def test_alert_triggered_when_below_threshold():
    # 0.6 < 0.8 * 0.90 = 0.72 → should alert
    assert should_alert_degradation(0.6, 0.8, sample_count=20)


def test_no_alert_when_above_threshold():
    # 0.75 >= 0.8 * 0.90 = 0.72 → no alert
    assert not should_alert_degradation(0.75, 0.8, sample_count=20)
