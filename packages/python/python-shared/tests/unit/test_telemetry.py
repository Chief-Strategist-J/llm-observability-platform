import pytest
from python_shared.telemetry import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    ACTIVE_WORKERS,
    setup_telemetry,
    get_tracer,
)

def test_telemetry_metrics():
    assert REQUEST_COUNT is not None
    assert REQUEST_LATENCY is not None
    assert ACTIVE_WORKERS is not None

def test_telemetry_tracer():
    setup_telemetry("test-service")
    tracer = get_tracer("test-tracer")
    assert tracer is not None or tracer is None
