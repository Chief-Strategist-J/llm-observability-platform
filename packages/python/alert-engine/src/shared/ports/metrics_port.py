from typing import Protocol

class MetricsPort(Protocol):
    def record_delivery_latency(self, alert_type: str, severity: str, latency_ms: float) -> None: ...
