import pytest
from infra.adapters.timesfm.timesfm_adapter import TimesFMAdapter

def test_timesfm_adapter_mock_fallback() -> None:
    # Test that the adapter handles initialization cleanly and falls back to a mock predictor
    adapter = TimesFMAdapter(repo_id="invalid-repo-id", backend="cpu")
    assert adapter.is_mock is True
    assert adapter.model is None

    # Run forecast and verify shape and results
    series = [1.0, 2.0, 3.0, 4.0, 5.0]
    horizon = 24
    mean, p10, p90 = adapter.forecast(series, horizon=horizon)

    assert len(mean) == horizon
    assert len(p10) == horizon
    assert len(p90) == horizon

    # Test values derived from avg of input series
    # Average of series is 3.0
    assert mean[0] == pytest.approx(3.0)
    assert p10[0] == pytest.approx(2.4)
    assert p90[0] == pytest.approx(3.6)


def test_timesfm_adapter_empty_series() -> None:
    adapter = TimesFMAdapter(repo_id="invalid-repo-id", backend="cpu")
    mean, p10, p90 = adapter.forecast([], horizon=24)
    assert len(mean) == 24
    assert all(val == 0.0 for val in mean)
