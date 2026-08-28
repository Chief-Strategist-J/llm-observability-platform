import base64
from datetime import date, datetime
from unittest.mock import MagicMock, patch
import pytest
from ddsketch import DDSketch
from ddsketch.pb.proto import DDSketchProto

from infra.adapters.clickhouse.clickhouse_adapter import ClickHouseAdapter
from infra.adapters.redis.redis_adapter import RedisAdapter
from infra.adapters.kafka.confluent_producer_adapter import ConfluentKafkaProducerAdapter
from features.latency_baseline.types import LatencyCheckpointResult

def test_latency_checkpoint_result_type() -> None:
    res = LatencyCheckpointResult(
        model="gpt-4",
        endpoint="/v1/chat/completions",
        checkpoint_date=date(2026, 6, 23),
        hour_of_day=14,
        p50_ttft_ms=10.0,
        p95_ttft_ms=20.0,
        p99_ttft_ms=30.0,
        p50_total_ms=100.0,
        p95_total_ms=200.0,
        p99_total_ms=300.0,
        sample_count=50,
        slo_violation_count=2
    )
    assert res.model == "gpt-4"
    assert res.sample_count == 50

@patch("clickhouse_connect.get_client")
def test_clickhouse_adapter(mock_get_client: MagicMock) -> None:
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    adapter = ClickHouseAdapter(
        host="localhost",
        port=8129,
        username="default",
        password="",
        database="default"
    )
    
    # Test insert
    adapter.insert_latency_checkpoints([("model", "endpoint", date(2026, 6, 23), 14, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 10, 1, datetime.now())])
    mock_client.insert.assert_called_once()
    
    # Test get history
    mock_client.query.return_value = MagicMock(result_rows=[(10.0,), (20.0,)])
    history = adapter.get_p99_ttft_history_7d("model", "endpoint", 14)
    assert history == [10.0, 20.0]

@patch("redis.Redis.from_url")
def test_redis_adapter(mock_from_url: MagicMock) -> None:
    mock_client = MagicMock()
    mock_from_url.return_value = mock_client
    
    adapter = RedisAdapter(url="redis://localhost:6389/0")
    
    # Test scan keys
    mock_client.keys.return_value = [b"key1", b"key2"]
    keys = adapter.scan_keys("pattern*")
    assert keys == ["key1", "key2"]
    
    # Test get key
    mock_client.get.return_value = b"value"
    val = adapter.get_key("key")
    assert val == "value"
    
    # Test get slo violation count
    mock_client.pipeline.return_value.execute.return_value = [b"1", b"2", None]
    err_count = adapter.get_slo_violation_count("model", "endpoint", 1719144000)
    assert err_count == 3
    
    # Test set baseline
    adapter.set_baseline_p99_ttft("model", "endpoint", 14, 15.5)
    mock_client.set.assert_called_once_with("baseline:p99_ttft:model:endpoint:14", "15.5")

@patch("infra.adapters.kafka.confluent_producer_adapter.Producer")
def test_confluent_producer_adapter(mock_producer_class: MagicMock) -> None:
    mock_prod = MagicMock()
    mock_producer_class.return_value = mock_prod
    
    adapter = ConfluentKafkaProducerAdapter(bootstrap_servers="localhost:9092")
    adapter.produce(topic="test", key="key", value=b"val")
    mock_prod.produce.assert_called_once()
    
    adapter.flush()
    mock_prod.flush.assert_called_once()
