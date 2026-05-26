from features.ewma_compute.service import EwmaService
from shared.types.ewma_types import EwmaRecord


def test_calculate_new_ewma() -> None:
    val = EwmaService.calculate_new_ewma(100.0, 50.0, 0.1)
    assert val == 55.0


def test_process_update_cold_start() -> None:
    record = EwmaService.process_update(120.0, None, 80.0)
    assert record.ewma_value == 80.0
    assert record.sample_count == 1
    assert record.is_cold_start is True


def test_process_update_under_7_samples() -> None:
    existing = EwmaRecord(
        service="srv",
        model="gpt-4",
        hour_of_week=42,
        ewma_value=50.0,
        sample_count=5,
        is_cold_start=True,
    )
    record = EwmaService.process_update(100.0, existing, 0.0)
    assert record.ewma_value == 55.0
    assert record.sample_count == 6
    assert record.is_cold_start is True


def test_process_update_transition_cold_start() -> None:
    existing = EwmaRecord(
        service="srv",
        model="gpt-4",
        hour_of_week=42,
        ewma_value=50.0,
        sample_count=6,
        is_cold_start=True,
    )
    record = EwmaService.process_update(100.0, existing, 0.0)
    assert record.ewma_value == 55.0
    assert record.sample_count == 7
    assert record.is_cold_start is False
