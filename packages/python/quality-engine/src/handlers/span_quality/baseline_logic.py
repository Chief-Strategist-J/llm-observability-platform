from __future__ import annotations
import math


def update_baseline_ewma(
    old_mean: float | None,
    new_score: float,
    window_count: int,
    max_window: int = 10080,  # 7 days × 1440 minutes/day
) -> float:
    """
    F-Q-07: Update rolling 7-day baseline using exponentially decaying count.
    Caps n at max_window to age out old data, preventing unbounded N dilution.
    Formula: new_mean = (old_mean × (n-1) + new_score) / n
             where n = min(window_count, max_window)
    """
    if old_mean is None:
        return new_score

    n = min(window_count, max_window)
    n = max(n, 1)
    return (old_mean * (n - 1) + new_score) / n


def should_alert_degradation(
    current_window_avg: float | None,
    baseline: float | None,
    sample_count: int,
    min_samples: int = 20,
    threshold_ratio: float = 0.90,
) -> bool:
    """
    F-Q-08: Return True if current 1-hour window avg < baseline × 0.90
    and sample_count >= 20. Both values must be non-null.
    """
    if current_window_avg is None or baseline is None:
        return False
    if sample_count < min_samples:
        return False
    return current_window_avg < (baseline * threshold_ratio)
