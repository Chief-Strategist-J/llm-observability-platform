import os
import time
import uuid
from datetime import datetime, timezone
import pytest
import allure
from src.infra.adapters.kafka.reliable_adapter import ReliableKafkaSpanReporter
from tests.unit.features.spans.test_reliable_reporter import FakeKafkaProducer, FakeWalStorage

@pytest.mark.performance
@allure.feature("Performance")
@allure.story("Span Reporter Performance")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("In-Memory Ingestion Throughput")
def test_reporter_in_memory_throughput():
    with allure.step("Initialize components"):
        producer = FakeKafkaProducer()
        wal = FakeWalStorage()
        reporter = ReliableKafkaSpanReporter(
            bootstrap_servers="localhost:9092",
            producer_port=producer,
            wal_port=wal,
            max_buffer_size=100000
        )
    with allure.step("Generate test spans"):
        num_spans = 5000
        spans = []
        for _ in range(num_spans):
            spans.append({
                "span_id": str(uuid.uuid4()),
                "trace_id": str(uuid.uuid4()),
                "schema_version": 1,
                "model": "gpt-4o",
                "provider": "openai",
                "service_name": "perf-service",
                "endpoint": "/v1/chat/completions",
                "environment": "production",
                "prompt_tokens": 150,
                "completion_tokens": 50,
                "latency_ms_total": 450,
                "finish_reason": "stop",
                "cost_usd_micro": 300,
                "price_version": "v1",
                "token_count_method": "tiktoken",
                "timestamp_utc": datetime.now(timezone.utc).isoformat()
            })
    with allure.step("Run benchmark"):
        start_time = time.time()
        for span in spans:
            reporter.report(span)
        end_time = time.time()
    with allure.step("Calculate and attach metrics"):
        duration = end_time - start_time
        throughput = num_spans / duration
        if hasattr(pytest, "performance_metrics"):
            pytest.performance_metrics["in_memory"] = {
                "throughput": throughput,
                "duration": duration,
                "spans": num_spans
            }
        print(f"\n[BENCHMARK] In-Memory Report Throughput: {throughput:.2f} spans/sec ({num_spans} spans in {duration:.4f}s)")
        allure.attach(
            f"Throughput: {throughput:.2f} spans/sec\nDuration: {duration:.4f}s\nSpans: {num_spans}",
            name="Throughput Metrics",
            attachment_type=allure.attachment_type.TEXT
        )
    with allure.step("Clean up"):
        reporter.close()
    assert duration < 1.0

@pytest.mark.performance
@allure.feature("Performance")
@allure.story("Span Reporter Performance")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("WAL Fallback Write Speed")
def test_reporter_wal_fallback_throughput():
    from src.infra.adapters.wal.sqlite_wal_adapter import SqliteWalStorageAdapter
    wal_db = "/tmp/llm-obs-wal-perf.db"
    with allure.step("Clean existing WAL"):
        if os.path.exists(wal_db):
            try:
                os.remove(wal_db)
            except OSError:
                pass
    with allure.step("Initialize components"):
        producer = FakeKafkaProducer()
        producer.fail_availability = True
        wal = SqliteWalStorageAdapter(wal_db)
        reporter = ReliableKafkaSpanReporter(
            bootstrap_servers="localhost:9092",
            producer_port=producer,
            wal_port=wal,
            max_buffer_size=1
        )
    with allure.step("Generate test spans"):
        num_spans = 1000
        spans = []
        for _ in range(num_spans):
            spans.append({
                "span_id": str(uuid.uuid4()),
                "trace_id": str(uuid.uuid4()),
                "schema_version": 1,
                "model": "gpt-4o",
                "provider": "openai",
                "service_name": "perf-service",
                "endpoint": "/v1/chat/completions",
                "environment": "production",
                "prompt_tokens": 150,
                "completion_tokens": 50,
                "latency_ms_total": 450,
                "finish_reason": "stop",
                "cost_usd_micro": 300,
                "price_version": "v1",
                "token_count_method": "tiktoken",
                "timestamp_utc": datetime.now(timezone.utc).isoformat()
            })
    with allure.step("Run benchmark"):
        start_time = time.time()
        for span in spans:
            reporter.report(span)
        end_time = time.time()
    with allure.step("Calculate and attach metrics"):
        duration = end_time - start_time
        throughput = num_spans / duration
        if hasattr(pytest, "performance_metrics"):
            pytest.performance_metrics["wal_fallback"] = {
                "throughput": throughput,
                "duration": duration,
                "spans": num_spans
            }
        print(f"\n[BENCHMARK] WAL Fallback Write Throughput: {throughput:.2f} spans/sec ({num_spans} spans in {duration:.4f}s)")
        allure.attach(
            f"Throughput: {throughput:.2f} spans/sec\nDuration: {duration:.4f}s\nSpans: {num_spans}",
            name="Throughput Metrics",
            attachment_type=allure.attachment_type.TEXT
        )
    with allure.step("Clean up"):
        reporter.close()
        if os.path.exists(wal_db):
            try:
                os.remove(wal_db)
            except OSError:
                pass

@pytest.mark.performance
@allure.feature("Performance")
@allure.story("Span Reporter Performance")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("WAL Replay Performance")
def test_reporter_wal_replay_throughput():
    from src.infra.adapters.wal.sqlite_wal_adapter import SqliteWalStorageAdapter
    wal_db = "/tmp/llm-obs-wal-perf-replay.db"
    with allure.step("Clean existing WAL"):
        if os.path.exists(wal_db):
            try:
                os.remove(wal_db)
            except OSError:
                pass
    with allure.step("Initialize components"):
        producer = FakeKafkaProducer()
        producer.fail_availability = True
        wal = SqliteWalStorageAdapter(wal_db)
        reporter = ReliableKafkaSpanReporter(
            bootstrap_servers="localhost:9092",
            producer_port=producer,
            wal_port=wal,
            max_buffer_size=1
        )
    with allure.step("Generate test spans in fallback"):
        num_spans = 500
        for _ in range(num_spans):
            reporter.report({
                "span_id": str(uuid.uuid4()),
                "trace_id": str(uuid.uuid4()),
                "schema_version": 1,
                "model": "gpt-4o",
                "provider": "openai",
                "service_name": "perf-service",
                "endpoint": "/v1/chat/completions",
                "environment": "production",
                "prompt_tokens": 150,
                "completion_tokens": 50,
                "latency_ms_total": 450,
                "finish_reason": "stop",
                "cost_usd_micro": 300,
                "price_version": "v1",
                "token_count_method": "tiktoken",
                "timestamp_utc": datetime.now(timezone.utc).isoformat()
            })
    with allure.step("Re-enable producer availability"):
        producer.fail_availability = False
        with reporter._lock:
            reporter._is_online = True
    with allure.step("Wait for WAL replay to complete"):
        start_time = time.time()
        while True:
            with reporter._lock:
                pending = reporter._wal_has_pending
            if not pending:
                break
            if time.time() - start_time > 10.0:
                break
            time.sleep(0.01)
    with allure.step("Calculate and attach metrics"):
        duration = time.time() - start_time
        throughput = num_spans / duration
        if hasattr(pytest, "performance_metrics"):
            pytest.performance_metrics["wal_replay"] = {
                "throughput": throughput,
                "duration": duration,
                "spans": num_spans
            }
        print(f"\n[BENCHMARK] WAL Replay Throughput: {throughput:.2f} spans/sec ({num_spans} spans in {duration:.4f}s)")
        allure.attach(
            f"Throughput: {throughput:.2f} spans/sec\nDuration: {duration:.4f}s\nSpans: {num_spans}",
            name="Throughput Metrics",
            attachment_type=allure.attachment_type.TEXT
        )
    with allure.step("Clean up"):
        reporter.close()
        if os.path.exists(wal_db):
            try:
                os.remove(wal_db)
            except OSError:
                pass
