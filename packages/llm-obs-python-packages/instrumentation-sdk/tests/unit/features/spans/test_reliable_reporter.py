import os
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple, Optional, Callable
from fastapi.testclient import TestClient

from src.shared.ports.kafka import KafkaProducerPort
from src.shared.ports.wal import WalStoragePort
from src.infra.adapters.kafka.reliable_adapter import ReliableKafkaSpanReporter
from src.features.spans.globals import set_reporter
from src.api.rest.v1.app import create_app

class FakeKafkaProducer(KafkaProducerPort):
    def __init__(self) -> None:
        self.messages: List[Tuple[str, Any, Any]] = []
        self.fail_availability = False
        self.fail_produce = False
        self.async_fail_delivery = False
        import threading
        self.block_produce: Optional[threading.Event] = None

    def produce(
        self,
        topic: str,
        key: Any,
        value: Any,
        on_delivery: Optional[Callable[[Any, Any], None]] = None
    ) -> None:
        if self.fail_produce:
            raise Exception("Kafka produce error")
        if self.block_produce:
            self.block_produce.wait()
        self.messages.append((topic, key, value))
        if on_delivery:
            if self.async_fail_delivery:
                on_delivery(Exception("Async Kafka delivery error"), None)
            else:
                on_delivery(None, object())

    def poll(self, timeout: float) -> int:
        return 0

    def flush(self, timeout: float) -> int:
        return 0

    def check_availability(self) -> bool:
        return not self.fail_availability

class FakeWalStorage(WalStoragePort):
    def __init__(self) -> None:
        self.records: List[Tuple[int, str, Any]] = []
        self.counter = 0
        self.initialized = False
        self.fail_save = False

    def initialize(self) -> None:
        self.initialized = True

    def save(self, span_id: str, span_json: Any) -> None:
        if self.fail_save:
            raise Exception("WAL save error")
        self.counter += 1
        self.records.append((self.counter, span_id, span_json))

    def save_batch(self, spans: List[Tuple[str, Any]]) -> None:
        if self.fail_save:
            raise Exception("WAL save error")
        for span_id, span_json in spans:
            self.counter += 1
            self.records.append((self.counter, span_id, span_json))

    def fetch_batch(self, limit: int) -> List[Tuple[int, str, Any]]:
        return self.records[:limit]

    def delete_batch(self, ids: List[int]) -> None:
        self.records = [r for r in self.records if r[0] not in ids]


def test_happy_path() -> None:
    producer = FakeKafkaProducer()
    wal = FakeWalStorage()
    reporter = ReliableKafkaSpanReporter(
        bootstrap_servers="localhost:9092",
        producer_port=producer,
        wal_port=wal
    )
    span_id = str(uuid.uuid4())
    span_data = {
        "span_id": span_id,
        "trace_id": str(uuid.uuid4()),
        "schema_version": 1,
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "test-service",
        "endpoint": "/api/test",
        "environment": "production",
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "latency_ms_total": 100,
        "finish_reason": "stop",
        "cost_usd_micro": 10,
        "price_version": "v1",
        "token_count_method": "tiktoken",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
    reporter.report(span_data)
    reporter.close()
    assert len(producer.messages) == 1
    assert producer.messages[0][1] == span_id
    assert len(wal.records) == 0

def test_wal_fallback_on_offline() -> None:
    producer = FakeKafkaProducer()
    producer.fail_availability = True
    wal = FakeWalStorage()
    reporter = ReliableKafkaSpanReporter(
        bootstrap_servers="localhost:9092",
        producer_port=producer,
        wal_port=wal
    )
    span_id = str(uuid.uuid4())
    span_data = {
        "span_id": span_id,
        "trace_id": str(uuid.uuid4()),
        "schema_version": 1,
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "test-service",
        "endpoint": "/api/test",
        "environment": "production",
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "latency_ms_total": 100,
        "finish_reason": "stop",
        "cost_usd_micro": 10,
        "price_version": "v1",
        "token_count_method": "tiktoken",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
    reporter.report(span_data)
    reporter.close()
    assert len(producer.messages) == 0
    assert len(wal.records) == 1
    assert wal.records[0][1] == span_id

def test_wal_fallback_on_buffer_full() -> None:
    import threading
    producer = FakeKafkaProducer()
    producer.block_produce = threading.Event()
    wal = FakeWalStorage()
    reporter = ReliableKafkaSpanReporter(
        bootstrap_servers="localhost:9092",
        max_buffer_size=1,
        producer_port=producer,
        wal_port=wal
    )
    span_data_1 = {
        "span_id": str(uuid.uuid4()),
        "schema_version": 1,
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "test-service",
        "endpoint": "/api/test",
        "environment": "production",
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "latency_ms_total": 100,
        "finish_reason": "stop",
        "cost_usd_micro": 10,
        "price_version": "v1",
        "token_count_method": "tiktoken",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
    span_data_2 = dict(span_data_1)
    span_data_2["span_id"] = str(uuid.uuid4())
    span_data_3 = dict(span_data_1)
    span_data_3["span_id"] = str(uuid.uuid4())
    
    reporter.report(span_data_1)
    reporter.report(span_data_2)
    reporter.report(span_data_3)
    
    import time
    time.sleep(0.2)
    
    assert len(wal.records) >= 1
    
    producer.block_produce.set()
    reporter.close()
    
    total_messages = len(producer.messages) + len(wal.records)
    assert total_messages == 3
    assert len(wal.records) == 0

def test_exception_suppression() -> None:
    producer = FakeKafkaProducer()
    producer.fail_produce = True
    wal = FakeWalStorage()
    wal.fail_save = True
    reporter = ReliableKafkaSpanReporter(
        bootstrap_servers="localhost:9092",
        producer_port=producer,
        wal_port=wal
    )
    span_data = {
        "span_id": str(uuid.uuid4()),
        "schema_version": 1,
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "test-service",
        "endpoint": "/api/test",
        "environment": "production",
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "latency_ms_total": 100,
        "finish_reason": "stop",
        "cost_usd_micro": 10,
        "price_version": "v1",
        "token_count_method": "tiktoken",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
    try:
        reporter.report(span_data)
    except Exception as e:
        pytest.fail(f"Exception raised in report: {e}")
    reporter.close()

def test_api_spans_endpoint() -> None:
    producer = FakeKafkaProducer()
    wal = FakeWalStorage()
    reporter = ReliableKafkaSpanReporter(
        bootstrap_servers="localhost:9092",
        producer_port=producer,
        wal_port=wal
    )
    set_reporter(reporter)
    
    os.environ["SKIP_APP_INIT"] = "true"
    app = create_app()
    client = TestClient(app)
    
    valid_payload = {
        "span_id": str(uuid.uuid4()),
        "schema_version": 1,
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "test-service",
        "endpoint": "/api/test",
        "environment": "production",
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "latency_ms_total": 100,
        "finish_reason": "stop",
        "cost_usd_micro": 10,
        "price_version": "v1",
        "token_count_method": "tiktoken",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
    
    response = client.post("/v1/spans", json=valid_payload)
    assert response.status_code == 202
    assert response.json()["success"] is True
    assert len(response.json()["span_warnings"]) == 0
    
    invalid_payload = dict(valid_payload)
    invalid_payload["prompt_tokens"] = 0
    response2 = client.post("/v1/spans", json=invalid_payload)
    assert response2.status_code == 400
    res_data2 = response2.json()
    assert "error" in res_data2
    assert res_data2["rule"] == "RULE-V-02"
    
    reporter.close()
