from prometheus_client import Counter, Histogram
from shared.ports.metrics_port import MetricsPort

WORKFLOW_RUN_LATENCY = Histogram(
    "quality_worker_run_latency_ms",
    "Quality baseline worker workflow run latency in milliseconds",
    ["workflow_name"]
)

BASELINE_UPDATES_TOTAL = Counter(
    "quality_baseline_updates_total",
    "Total quality baseline keys updated in Redis",
)

ROLLUP_ROWS_TOTAL = Counter(
    "quality_rollup_rows_total",
    "Total rows rolled up into ClickHouse quality_trend",
)

class PrometheusAdapter(MetricsPort):
    def record_workflow_run_latency(self, workflow_name: str, latency_ms: float) -> None:
        WORKFLOW_RUN_LATENCY.labels(workflow_name=workflow_name).observe(latency_ms)

    def record_baseline_updates(self, count: int) -> None:
        if count > 0:
            BASELINE_UPDATES_TOTAL.inc(count)

    def record_rollup_rows(self, count: int) -> None:
        if count > 0:
            ROLLUP_ROWS_TOTAL.inc(count)
