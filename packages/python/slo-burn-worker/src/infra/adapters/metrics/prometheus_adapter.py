from prometheus_client import Counter
from shared.ports.metrics_port import MetricsPort

ALERTS_SENT_TOTAL = Counter(
    "slo_alerts_sent_total",
    "Total SLO alerts sent",
    ["model", "endpoint", "severity"]
)

ALERTS_DEDUPED_TOTAL = Counter(
    "slo_alerts_deduped_total",
    "Total SLO alerts deduplicated (suppressed)",
    ["model", "endpoint", "severity"]
)

BURN_RATE_COMPUTED_TOTAL = Counter(
    "slo_burn_rate_computed_total",
    "Total SLO burn rates computed",
    ["model", "endpoint"]
)

class PrometheusAdapter(MetricsPort):
    def record_alert_sent(self, model: str, endpoint: str, severity: str) -> None:
        ALERTS_SENT_TOTAL.labels(model=model, endpoint=endpoint, severity=severity).inc()

    def record_alert_deduped(self, model: str, endpoint: str, severity: str) -> None:
        ALERTS_DEDUPED_TOTAL.labels(model=model, endpoint=endpoint, severity=severity).inc()

    def record_burn_rate_computed(self, model: str, endpoint: str) -> None:
        BURN_RATE_COMPUTED_TOTAL.labels(model=model, endpoint=endpoint).inc()
