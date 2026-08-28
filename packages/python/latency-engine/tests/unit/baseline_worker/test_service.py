import pytest
import base64
from datetime import date
from unittest.mock import MagicMock
from ddsketch import DDSketch
from ddsketch.pb.proto import DDSketchProto
from features.latency_baseline.service import LatencyBaselineService

def serialize_sketch(sketch: DDSketch) -> str:
    proto_msg = DDSketchProto.to_proto(sketch)
    return base64.b64encode(proto_msg.SerializeToString()).decode('utf-8')

def test_service_run_hourly_checkpoint() -> None:
    # Prepare sketches
    ttft_sketch = DDSketch(relative_accuracy=0.01)
    ttft_sketch.add(10.0)
    ttft_sketch.add(20.0)
    ttft_b64 = serialize_sketch(ttft_sketch)

    total_sketch = DDSketch(relative_accuracy=0.01)
    total_sketch.add(100.0)
    total_sketch.add(200.0)
    total_b64 = serialize_sketch(total_sketch)

    # Setup mocks
    redis_mock = MagicMock()
    redis_mock.scan_keys.side_effect = lambda pat: (
        ["sketch:ttft:gpt-4:14"] if "ttft" in pat else ["sketch:total:gpt-4:/v1/chat/completions:14"]
    )
    redis_mock.get_key.side_effect = lambda k: (
        ttft_b64 if "ttft" in k else total_b64
    )
    redis_mock.get_slo_violation_count.return_value = 2

    clickhouse_mock = MagicMock()
    clickhouse_mock.get_p99_ttft_history_7d.return_value = [20.0] * 8

    kafka_mock = MagicMock()

    count = LatencyBaselineService.run_hourly_checkpoint(
        redis=redis_mock,
        clickhouse=clickhouse_mock,
        kafka=kafka_mock,
        target_date=date(2026, 6, 23),
        target_hour=14
    )

    assert count == 1
    clickhouse_mock.insert_latency_checkpoints.assert_called_once()
    kafka_mock.produce.assert_not_called()

def test_service_ttft_regression_alert() -> None:
    # Prepare sketches
    ttft_sketch = DDSketch(relative_accuracy=0.01)
    # Adding values to get a high p99_ttft
    for _ in range(30):
        ttft_sketch.add(50.0)
    ttft_b64 = serialize_sketch(ttft_sketch)

    total_sketch = DDSketch(relative_accuracy=0.01)
    for _ in range(30):
        total_sketch.add(100.0)
    total_b64 = serialize_sketch(total_sketch)

    # Setup mocks
    redis_mock = MagicMock()
    redis_mock.scan_keys.side_effect = lambda pat: (
        ["sketch:ttft:gpt-4:14"] if "ttft" in pat else ["sketch:total:gpt-4:/v1/chat/completions:14"]
    )
    redis_mock.get_key.side_effect = lambda k: (
        ttft_b64 if "ttft" in k else total_b64
    )
    redis_mock.get_slo_violation_count.return_value = 0

    clickhouse_mock = MagicMock()
    # History shows a baseline p99_ttft_ms of 10.0
    # The current p99_ttft_ms is 50.0. Since 50.0 > 2 * 10.0 and sample count (30) >= 30, it should trigger alert!
    clickhouse_mock.get_p99_ttft_history_7d.return_value = [50.0] + [10.0] * 7

    kafka_mock = MagicMock()

    count = LatencyBaselineService.run_hourly_checkpoint(
        redis=redis_mock,
        clickhouse=clickhouse_mock,
        kafka=kafka_mock,
        target_date=date(2026, 6, 23),
        target_hour=14
    )

    assert count == 1
    kafka_mock.produce.assert_called_once()
