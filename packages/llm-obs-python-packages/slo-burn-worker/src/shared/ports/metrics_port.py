from typing import Protocol

class MetricsPort(Protocol):
    def record_alert_sent(self, model: str, endpoint: str, severity: str) -> None:
        """Records telemetry metric for sent alert."""
        ...

    def record_alert_deduped(self, model: str, endpoint: str, severity: str) -> None:
        """Records telemetry metric for deduped alerts."""
        ...

    def record_burn_rate_computed(self, model: str, endpoint: str) -> None:
        """Records metric for burn rate computations."""
        ...
