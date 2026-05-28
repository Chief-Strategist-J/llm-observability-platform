from prometheus_client import Counter, Histogram
from shared.ports.metrics_port import MetricsPort

WORKFLOW_RUN_LATENCY = Histogram(
    "ewma_worker_run_latency_ms",
    "EWMA worker workflow run latency in milliseconds"
)

COLD_START_TOTAL = Counter(
    "ewma_cold_start_total",
    "Total cold starts observed",
    ["service", "model"]
)

RETROACTIVE_CORRECTION_TOTAL = Counter(
    "retroactive_correction_applied_total",
    "Total retroactive cost corrections applied",
    ["model"]
)

INTEGRITY_MISMATCH_TOTAL = Counter(
    "fenwick_integrity_mismatch_total",
    "Total Fenwick Tree vs ClickHouse integrity mismatches",
    ["dimension"]
)

class PrometheusAdapter(MetricsPort):
    def record_workflow_run_latency(self, latency_ms: float) -> None:
        WORKFLOW_RUN_LATENCY.observe(latency_ms)

    def record_cold_start(self, service: str, model: str) -> None:
        COLD_START_TOTAL.labels(service=service, model=model).inc()

    def record_retroactive_correction(self, model: str, count: int) -> None:
        RETROACTIVE_CORRECTION_TOTAL.labels(model=model).inc(count)

    def record_integrity_mismatch(self, dimension: str) -> None:
        INTEGRITY_MISMATCH_TOTAL.labels(dimension=dimension).inc()
