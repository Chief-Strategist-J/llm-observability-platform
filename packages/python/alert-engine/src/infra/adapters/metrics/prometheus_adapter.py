from prometheus_client import Histogram
from shared.ports.metrics_port import MetricsPort

class PrometheusAdapter(MetricsPort):
    def __init__(self) -> None:
        self._histogram = Histogram(
            "alert_delivery_latency_ms",
            "Alert delivery latency in milliseconds",
            ["type", "severity"]
        )

    def record_delivery_latency(self, alert_type: str, severity: str, latency_ms: float) -> None:
        self._histogram.labels(type=alert_type, severity=severity).observe(latency_ms)
