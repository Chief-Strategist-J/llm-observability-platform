from __future__ import annotations
import pytest
from datetime import datetime
import redis

from handlers.latency_handler import LatencyHandler

class MockRedis:
    def __init__(self) -> None:
        self.data: dict[str, bytes] = {}
        self.lists: dict[str, list[float]] = {}
        self.hashes: dict[str, dict[str, str]] = {}
        self.ttls: dict[str, int] = {}
        self.fail = False

    def ping(self):
        if self.fail:
            raise redis.exceptions.ConnectionError("Redis down")
        return True

    def get(self, key: str):
        if self.fail:
            raise redis.exceptions.ConnectionError("Redis down")
        return self.data.get(key)

    def set(self, key: str, value: str):
        if self.fail:
            raise redis.exceptions.ConnectionError("Redis down")
        self.data[key] = value.encode('utf-8')
        return True

    def lpush(self, key: str, value: float):
        if self.fail:
            raise redis.exceptions.ConnectionError("Redis down")
        self.lists.setdefault(key, []).insert(0, value)

    def ltrim(self, key: str, start: int, end: int):
        if self.fail:
            raise redis.exceptions.ConnectionError("Redis down")
        if key in self.lists:
            self.lists[key] = self.lists[key][start:end+1]

    def hset(self, key: str, mapping: dict):
        if self.fail:
            raise redis.exceptions.ConnectionError("Redis down")
        self.hashes.setdefault(key, {}).update(mapping)

    def hincrbyfloat(self, key: str, field: str, amount: float):
        if self.fail:
            raise redis.exceptions.ConnectionError("Redis down")
        h = self.hashes.setdefault(key, {})
        val = float(h.get(field, "0.0")) + amount
        h[field] = str(val)

    def incr(self, key: str):
        if self.fail:
            raise redis.exceptions.ConnectionError("Redis down")
        h = self.hashes.setdefault("incr_counters", {})
        val = int(h.get(key, "0")) + 1
        h[key] = str(val)

    def expire(self, key: str, seconds: int):
        if self.fail:
            raise redis.exceptions.ConnectionError("Redis down")
        self.ttls[key] = seconds

    def pipeline(self):
        if self.fail:
            raise redis.exceptions.ConnectionError("Redis down")
        return self

    def execute(self):
        if self.fail:
            raise redis.exceptions.ConnectionError("Redis down")
        return []

class MockMetrics:
    def __init__(self) -> None:
        self.processed = []
        self.dropped = []

    def record_span_processed(self, model: str, endpoint: str, retry_count: int) -> None:
        self.processed.append((model, endpoint, retry_count))

    def record_sketch_dropped(self, key: str, count: int) -> None:
        self.dropped.append((key, count))

@pytest.fixture
def mock_redis() -> MockRedis:
    return MockRedis()

@pytest.fixture
def temp_slo_config(tmp_path) -> str:
    cfg = tmp_path / "slo_config.yaml"
    cfg.write_text("""
endpoints:
  /v1/chat/completions: 1000
  default: 500
""")
    return str(cfg)

# ==============================================================================
# F-L-01, F-L-05: DDSketch updates & Retry separation
# ==============================================================================
def test_ddsketch_updates(mock_redis, temp_slo_config):
    mock_metrics = MockMetrics()
    handler = LatencyHandler(mock_redis, temp_slo_config, metrics=mock_metrics)
    
    spans = [
        # 1. Normal streaming span (no retry)
        {
            "span_id": "span-1",
            "model": "gpt-4",
            "endpoint": "/v1/chat/completions",
            "latency_ms_ttft": 150,
            "latency_ms_total": 1200,
            "retry_count": 0,
            "timestamp_utc": "2026-06-17T08:30:00Z"
        },
        # 2. Non-streaming span (no TTFT, no retry)
        {
            "span_id": "span-2",
            "model": "gpt-4",
            "endpoint": "/v1/chat/completions",
            "latency_ms_ttft": None,
            "latency_ms_total": 800,
            "retry_count": 0,
            "timestamp_utc": "2026-06-17T08:30:00Z"
        },
        # 3. Retry span
        {
            "span_id": "span-3",
            "model": "gpt-4",
            "endpoint": "/v1/chat/completions",
            "latency_ms_ttft": 200,
            "latency_ms_total": 2500,
            "retry_count": 1,
            "timestamp_utc": "2026-06-17T08:30:00Z"
        }
    ]
    
    handler.handle_spans(spans)
    
    # Verify TTFT sketch
    ttft_key = "sketch:ttft:gpt-4:8"
    assert ttft_key in mock_redis.data
    ttft_sketch = handler._deserialize_sketch(mock_redis.data[ttft_key].decode('utf-8'))
    # gpt-4 has ttft for span-1 (150) and span-3 (200) -> count = 2
    assert ttft_sketch.count == 2
    
    # Verify Total sketch (excludes retry spans)
    total_key = "sketch:total:gpt-4:/v1/chat/completions:8"
    assert total_key in mock_redis.data
    total_sketch = handler._deserialize_sketch(mock_redis.data[total_key].decode('utf-8'))
    # gpt-4 non-retry total latency for span-1 (1200) and span-2 (800) -> count = 2
    assert total_sketch.count == 2

    # Verify All attempts sketch
    all_attempts_key = "sketch:total:gpt-4:8"
    assert all_attempts_key in mock_redis.data
    all_attempts_sketch = handler._deserialize_sketch(mock_redis.data[all_attempts_key].decode('utf-8'))
    assert all_attempts_sketch.count == 3

    # Verify First attempts only sketch
    no_retry_key = "sketch:total:no_retry:gpt-4:8"
    assert no_retry_key in mock_redis.data
    no_retry_sketch = handler._deserialize_sketch(mock_redis.data[no_retry_key].decode('utf-8'))
    assert no_retry_sketch.count == 2

    # Verify Retry sketch
    retry_key = "sketch:total:retry:gpt-4"
    assert retry_key in mock_redis.data
    retry_sketch = handler._deserialize_sketch(mock_redis.data[retry_key].decode('utf-8'))
    # gpt-4 retry total latency for span-3 (2500) -> count = 1
    assert retry_sketch.count == 1

    # Verify MetricsPort calls
    assert len(mock_metrics.processed) == 3
    assert mock_metrics.processed[0] == ("gpt-4", "/v1/chat/completions", 0)
    assert mock_metrics.processed[1] == ("gpt-4", "/v1/chat/completions", 0)
    assert mock_metrics.processed[2] == ("gpt-4", "/v1/chat/completions", 1)



# ==============================================================================
# F-L-02: TPOT computation
# ==============================================================================
def test_tpot_computation(mock_redis, temp_slo_config):
    handler = LatencyHandler(mock_redis, temp_slo_config)
    
    spans = [
        # Normal TPOT: tpot_ms = (1200 - 200) / 10 = 100.0
        {
            "span_id": "span-1",
            "model": "gpt-4",
            "endpoint": "/v1/chat/completions",
            "latency_ms_ttft": 200,
            "latency_ms_total": 1200,
            "completion_tokens": 10,
            "finish_reason": "stop"
        },
        # Skipped TPOT: finish_reason is timeout
        {
            "span_id": "span-2",
            "model": "gpt-4",
            "endpoint": "/v1/chat/completions",
            "latency_ms_ttft": 200,
            "latency_ms_total": 1200,
            "completion_tokens": 10,
            "finish_reason": "timeout"
        }
    ]
    
    handler.handle_spans(spans)
    
    tpot_key = "tpot:latest:gpt-4"
    assert tpot_key in mock_redis.lists
    # Only span-1 is processed
    assert len(mock_redis.lists[tpot_key]) == 1
    assert mock_redis.lists[tpot_key][0] == 100.0


# ==============================================================================
# F-L-03: SLO error counter update
# ==============================================================================
def test_slo_counter_update(mock_redis, temp_slo_config):
    handler = LatencyHandler(mock_redis, temp_slo_config)
    
    spans = [
        # Above threshold (1200 > 1000)
        {
            "span_id": "span-1",
            "model": "gpt-4",
            "endpoint": "/v1/chat/completions",
            "latency_ms_total": 1200,
            "timestamp_utc": "2026-06-17T08:30:00Z"
        },
        # Below threshold (800 <= 1000)
        {
            "span_id": "span-2",
            "model": "gpt-4",
            "endpoint": "/v1/chat/completions",
            "latency_ms_total": 800,
            "timestamp_utc": "2026-06-17T08:30:00Z"
        }
    ]
    
    handler.handle_spans(spans)
    
    dt = datetime.fromisoformat("2026-06-17T08:30:00+00:00")
    bucket = int(dt.timestamp()) // 60
    total_key = f"slo:total:gpt-4:/v1/chat/completions:{bucket}"
    err_key = f"slo:errors:gpt-4:/v1/chat/completions:{bucket}"
    
    counters = mock_redis.hashes["incr_counters"]
    assert counters[total_key] == "2"
    assert counters[err_key] == "1"
    
    # Check TTL expire set to 6 hours = 21600s
    assert mock_redis.ttls[total_key] == 21600
    assert mock_redis.ttls[err_key] == 21600


# ==============================================================================
# F-L-04: Latency attribution
# ==============================================================================
def test_latency_attribution(mock_redis, temp_slo_config):
    handler = LatencyHandler(mock_redis, temp_slo_config)
    
    spans = [
        {
            "span_id": "span-123",
            "model": "gpt-4",
            "endpoint": "/v1/chat/completions",
            "latency_ms_total": 1000,
            "timestamp_utc": "2026-06-17T08:30:00Z",
            "attributes": {
                "net.dns.latency_ms": 15.5,
                "net.tcp.latency_ms": 25.0,
                "llm.queue.latency_ms": 100.0,
                "llm.inference.latency_ms": 800.0
            }
        }
    ]
    
    handler.handle_spans(spans)
    
    # Hash check
    hash_key = "attribution:span-123"
    assert hash_key in mock_redis.hashes
    assert mock_redis.hashes[hash_key]["dns"] == "15.5"
    assert mock_redis.hashes[hash_key]["inference"] == "800.0"
    assert mock_redis.ttls[hash_key] == 300
    
    # Hourly aggregation check
    agg_key = "attr:avg:gpt-4:2026061708"
    assert agg_key in mock_redis.hashes
    assert mock_redis.hashes[agg_key]["dns"] == "15.5"
    assert mock_redis.hashes[agg_key]["queue"] == "100.0"


# ==============================================================================
# F-L-06: Dead letter / buffering updates
# ==============================================================================
def test_dead_letter_buffering(mock_redis, temp_slo_config):
    handler = LatencyHandler(mock_redis, temp_slo_config)
    
    # Simulate Redis connection failure
    mock_redis.fail = True
    
    spans = [
        {
            "span_id": "span-1",
            "model": "gpt-4",
            "endpoint": "/v1/chat/completions",
            "latency_ms_total": 1200,
            "timestamp_utc": "2026-06-17T08:30:00Z"
        }
    ]
    
    handler.handle_spans(spans)
    
    # Sketch updates should be buffered
    assert len(handler.redis_buffer) > 0
    total_key = "sketch:total:gpt-4:/v1/chat/completions:8"
    assert total_key in handler.redis_buffer
    assert handler.redis_buffer[total_key] == [1200.0]
    
    # Simulate Redis recovery
    mock_redis.fail = False
    
    # Next handle_spans call triggers recovery/replay
    handler.handle_spans([])
    
    # Buffer should be replayed and cleared
    assert len(handler.redis_buffer) == 0
    assert total_key in mock_redis.data
