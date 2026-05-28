from typing import Protocol

class MetricsPort(Protocol):
    def record_workflow_run_latency(self, latency_ms: float) -> None:
        ...

    def record_cold_start(self, service: str, model: str) -> None:
        ...

    def record_retroactive_correction(self, model: str, count: int) -> None:
        ...

    def record_integrity_mismatch(self, dimension: str) -> None:
        ...
