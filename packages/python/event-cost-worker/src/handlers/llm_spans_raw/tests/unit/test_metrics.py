from infra.adapters.metrics.prometheus_adapter import PrometheusAdapter

def test_prometheus_adapter():
    adapter = PrometheusAdapter()
    adapter.record_processed_span("test-service", "gpt-4")
    adapter.record_fenwick_latency(5.5)
    adapter.record_redis_pipeline_latency(12.3)
    adapter.record_dlq_event("deserialization_error")
    adapter.record_kafka_lag(0, 150)
