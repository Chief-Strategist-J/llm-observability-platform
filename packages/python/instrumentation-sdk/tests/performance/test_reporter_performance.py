import os
import time
import uuid
import math
import resource
import pytest
import allure
from src.infra.adapters.kafka.reliable_adapter import ReliableKafkaSpanReporter
from tests.unit.features.spans.test_reliable_reporter import FakeKafkaProducer, FakeWalStorage
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult

class InMemoryExporter(SpanExporter):
    def __init__(self) -> None:
        self.spans = []

    def export(self, spans) -> SpanExportResult:
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass

def calculate_percentile(data, q):
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (q / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return d0 + d1

def get_resources():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "cpu_time": usage.ru_utime + usage.ru_stime,
        "max_rss": usage.ru_maxrss / 1024.0
    }

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
                "timestamp_utc": datetime_utc_str()
            })
    with allure.step("Run benchmark"):
        res_start = get_resources()
        start_time = time.perf_counter()
        latencies = []
        for span in spans:
            t0 = time.perf_counter()
            reporter.report(span)
            latencies.append(time.perf_counter() - t0)
        end_time = time.perf_counter()
        res_end = get_resources()
    with allure.step("Calculate and attach metrics"):
        duration = end_time - start_time
        throughput = num_spans / duration
        latencies_ms = [l * 1000.0 for l in latencies]
        p50 = calculate_percentile(latencies_ms, 50)
        p95 = calculate_percentile(latencies_ms, 95)
        p99 = calculate_percentile(latencies_ms, 99)
        cpu_spent = res_end["cpu_time"] - res_start["cpu_time"]
        max_rss = res_end["max_rss"]
        if hasattr(pytest, "performance_metrics"):
            pytest.performance_metrics["in_memory"] = {
                "throughput": throughput,
                "duration": duration,
                "spans": num_spans,
                "p50": p50,
                "p95": p95,
                "p99": p99,
                "cpu_time": cpu_spent,
                "max_rss": max_rss
            }
        allure.attach(
            f"Throughput: {throughput:.2f} spans/sec\nDuration: {duration:.4f}s\nSpans: {num_spans}\np50: {p50:.2f}ms\np95: {p95:.2f}ms\np99: {p99:.2f}ms\nCPU Time: {cpu_spent:.4f}s\nMemory RSS: {max_rss:.2f}MB",
            name="Throughput Metrics",
            attachment_type=allure.attachment_type.TEXT
        )
    with allure.step("Clean up"):
        reporter.close()

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
                "timestamp_utc": datetime_utc_str()
            })
    with allure.step("Run benchmark"):
        res_start = get_resources()
        start_time = time.perf_counter()
        latencies = []
        for span in spans:
            t0 = time.perf_counter()
            reporter.report(span)
            latencies.append(time.perf_counter() - t0)
        
        reporter.close()
        end_time = time.perf_counter()
        res_end = get_resources()
    with allure.step("Calculate and attach metrics"):
        duration = end_time - start_time
        throughput = num_spans / duration
        latencies_ms = [l * 1000.0 for l in latencies]
        p50 = calculate_percentile(latencies_ms, 50)
        p95 = calculate_percentile(latencies_ms, 95)
        p99 = calculate_percentile(latencies_ms, 99)
        cpu_spent = res_end["cpu_time"] - res_start["cpu_time"]
        max_rss = res_end["max_rss"]
        if hasattr(pytest, "performance_metrics"):
            pytest.performance_metrics["wal_fallback"] = {
                "throughput": throughput,
                "duration": duration,
                "spans": num_spans,
                "p50": p50,
                "p95": p95,
                "p99": p99,
                "cpu_time": cpu_spent,
                "max_rss": max_rss
            }
        allure.attach(
            f"Throughput: {throughput:.2f} spans/sec\nDuration: {duration:.4f}s\nSpans: {num_spans}\np50: {p50:.2f}ms\np95: {p95:.2f}ms\np99: {p99:.2f}ms\nCPU Time: {cpu_spent:.4f}s\nMemory RSS: {max_rss:.2f}MB",
            name="Throughput Metrics",
            attachment_type=allure.attachment_type.TEXT
        )
    with allure.step("Clean up"):
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
            max_buffer_size=100000
        )
    with allure.step("Generate test spans in fallback"):
        num_spans = 5000
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
                "timestamp_utc": datetime_utc_str()
            })
    with allure.step("Re-enable producer availability and start timer"):
        producer.fail_availability = False
        res_start = get_resources()
        start_time = time.perf_counter()
        with reporter._lock:
            reporter._is_online = True
    with allure.step("Wait for WAL replay to complete"):
        while True:
            with reporter._lock:
                pending = reporter._wal_has_pending
            if not pending:
                records = wal.fetch_batch(1)
                if not records:
                    break
            time.sleep(0.005)
        end_time = time.perf_counter()
        res_end = get_resources()
    with allure.step("Calculate and attach metrics"):
        duration = end_time - start_time
        throughput = num_spans / duration
        cpu_spent = res_end["cpu_time"] - res_start["cpu_time"]
        max_rss = res_end["max_rss"]
        if hasattr(pytest, "performance_metrics"):
            pytest.performance_metrics["wal_replay"] = {
                "throughput": throughput,
                "duration": duration,
                "spans": num_spans,
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "cpu_time": cpu_spent,
                "max_rss": max_rss
            }
        allure.attach(
            f"Throughput: {throughput:.2f} spans/sec\nDuration: {duration:.4f}s\nSpans: {num_spans}\nCPU Time: {cpu_spent:.4f}s\nMemory RSS: {max_rss:.2f}MB",
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
@allure.title("OpenTelemetry SDK Throughput Comparison")
def test_otel_sdk_comparison_throughput():
    with allure.step("Initialize OTel SDK components"):
        provider = TracerProvider()
        exporter = InMemoryExporter()
        processor = BatchSpanProcessor(exporter, max_queue_size=100000, max_export_batch_size=512)
        provider.add_span_processor(processor)
        tracer = provider.get_tracer("otel-perf")
    with allure.step("Generate spans through OTel Tracer"):
        num_spans = 5000
        res_start = get_resources()
        start_time = time.perf_counter()
        latencies = []
        for i in range(num_spans):
            t0 = time.perf_counter()
            with tracer.start_as_current_span(f"span_{i}") as s:
                s.set_attribute("model", "gpt-4o")
                s.set_attribute("provider", "openai")
                s.set_attribute("prompt_tokens", 150)
                s.set_attribute("completion_tokens", 50)
            latencies.append(time.perf_counter() - t0)
        processor.shutdown()
        end_time = time.perf_counter()
        res_end = get_resources()
    with allure.step("Calculate and attach metrics"):
        duration = end_time - start_time
        throughput = num_spans / duration
        latencies_ms = [l * 1000.0 for l in latencies]
        p50 = calculate_percentile(latencies_ms, 50)
        p95 = calculate_percentile(latencies_ms, 95)
        p99 = calculate_percentile(latencies_ms, 99)
        cpu_spent = res_end["cpu_time"] - res_start["cpu_time"]
        max_rss = res_end["max_rss"]
        if hasattr(pytest, "performance_metrics"):
            pytest.performance_metrics["otel_comparison"] = {
                "throughput": throughput,
                "duration": duration,
                "spans": num_spans,
                "p50": p50,
                "p95": p95,
                "p99": p99,
                "cpu_time": cpu_spent,
                "max_rss": max_rss
            }
        allure.attach(
            f"Throughput: {throughput:.2f} spans/sec\nDuration: {duration:.4f}s\nSpans: {num_spans}\np50: {p50:.2f}ms\np95: {p95:.2f}ms\np99: {p99:.2f}ms\nCPU Time: {cpu_spent:.4f}s\nMemory RSS: {max_rss:.2f}MB",
            name="Throughput Metrics",
            attachment_type=allure.attachment_type.TEXT
        )

def datetime_utc_str() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

