from typing import Protocol, Dict


class MetricsPort(Protocol):
    def record_tokens(self, amount: int, labels: Dict[str, str]) -> None:
        ...

    def record_cost(self, amount: int, labels: Dict[str, str]) -> None:
        ...

    def record_latency(self, duration_ms: int, labels: Dict[str, str]) -> None:
        ...

    def record_ttft(self, duration_ms: int, labels: Dict[str, str]) -> None:
        ...

    def record_pii(self, labels: Dict[str, str]) -> None:
        ...

    def record_injection(self, labels: Dict[str, str]) -> None:
        ...

    def record_finish_reason(self, labels: Dict[str, str]) -> None:
        ...

    def record_span(self, labels: Dict[str, str]) -> None:
        ...
