import logging
from datetime import datetime, timedelta
import pytest
from features.forecast.service import ForecastService


def test_build_dense_series_success() -> None:
    # Behavior: builds a dense hourly series with correct values in correct bins
    anchor = datetime(2026, 6, 21, 10, 0, 0)
    # We need 48 data points to satisfy the default min_history_hours=48 constraint
    raw_rows = []
    # Add 50 data points spanning the last 50 hours
    for i in range(50):
        t = anchor - timedelta(hours=i)
        raw_rows.append(("service-a", "model-b", t, 10.0 + i))

    dense, skip = ForecastService.build_dense_series(
        raw_rows, lookback_hours=168, min_history_hours=48, anchor_time=anchor
    )

    pair = ("service-a", "model-b")
    assert pair in dense
    assert len(dense[pair]) == 168
    assert len(skip) == 0

    # The bucket at anchor is at index 167 (last bucket)
    assert dense[pair][167] == 10.0
    # The bucket 1 hour ago is at index 166
    assert dense[pair][166] == 11.0
    # Values before the 50 hours should be 0.0
    assert dense[pair][0] == 0.0


def test_build_dense_series_skipped_insufficient_history(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Behavior: skips pairs that have history length less than min_history_hours
    anchor = datetime(2026, 6, 21, 10, 0, 0)
    raw_rows = []
    # Add only 10 data points
    for i in range(10):
        t = anchor - timedelta(hours=i)
        raw_rows.append(("service-a", "model-b", t, 100.0))

    with caplog.at_level(logging.INFO):
        dense, skip = ForecastService.build_dense_series(
            raw_rows, lookback_hours=168, min_history_hours=48, anchor_time=anchor
        )

    pair = ("service-a", "model-b")
    assert pair not in dense
    assert pair in skip
    assert "forecast_skipped_insufficient_history_total" in caplog.text
    assert "service=service-a" in caplog.text
    assert "model=model-b" in caplog.text


def test_build_dense_series_empty_input() -> None:
    # Behavior: returns empty dense series and empty skip list for empty raw rows
    dense, skip = ForecastService.build_dense_series(
        [], lookback_hours=168, min_history_hours=48
    )
    assert len(dense) == 0
    assert len(skip) == 0


def test_build_dense_series_out_of_bounds_ignored() -> None:
    # Behavior: ignores data points that lie outside the lookback window
    anchor = datetime(2026, 6, 21, 10, 0, 0)
    raw_rows = []
    # Add 48 points inside lookback window
    for i in range(48):
        t = anchor - timedelta(hours=i)
        raw_rows.append(("service-a", "model-b", t, 10.0))
    # Add 10 points older than 168 hours ago
    for i in range(200, 210):
        t = anchor - timedelta(hours=i)
        raw_rows.append(("service-a", "model-b", t, 1000.0))

    dense, skip = ForecastService.build_dense_series(
        raw_rows, lookback_hours=168, min_history_hours=48, anchor_time=anchor
    )

    pair = ("service-a", "model-b")
    assert pair in dense
    assert len(skip) == 0
    # None of the 1000.0 values should be in the lookback series
    assert 1000.0 not in dense[pair]
