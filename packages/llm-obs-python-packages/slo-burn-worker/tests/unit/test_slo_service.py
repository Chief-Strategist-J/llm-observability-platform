import pytest
from features.slo.service import SloService

def test_get_window_buckets():
    buckets = SloService.get_window_buckets(100, 5)
    assert buckets == [95, 96, 97, 98, 99]

def test_compute_burn_rate():
    # Errors/total/slo_threshold
    # error_rate = 5/100 = 0.05
    # slo_eb = 1.0 - 0.95 = 0.05
    # burn_rate = 0.05 / 0.05 = 1.0
    burn = SloService.compute_burn_rate(5, 100, 0.95)
    assert burn == pytest.approx(1.0)

    # total = 0
    assert SloService.compute_burn_rate(5, 0, 0.95) == 0.0

def test_determine_severity():
    # page
    assert SloService.determine_severity(15.0, 6.1, 2.0) == "page"
    # slack
    assert SloService.determine_severity(1.0, 6.1, 3.1) == "slack"
    # ticket
    assert SloService.determine_severity(0.5, 2.0, 1.1) == "ticket"
    # None
    assert SloService.determine_severity(0.5, 0.5, 0.5) is None

def test_compute_budget_remaining_pct():
    # total_calls = 10000, threshold = 0.95 (EB = 0.05) -> budget = 500
    # errors = 100
    # remaining_pct = (500 - 100) / 500 * 100 = 80%
    pct = SloService.compute_budget_remaining_pct(100, 10000, 0.95)
    assert pct == pytest.approx(80.0)

    # budget <= 0 (e.g. total_calls = 0)
    assert SloService.compute_budget_remaining_pct(0, 0, 0.95) == 100.0
    assert SloService.compute_budget_remaining_pct(10, 0, 0.95) == 0.0
