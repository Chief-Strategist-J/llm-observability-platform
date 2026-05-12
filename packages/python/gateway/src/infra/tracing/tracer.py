"""OpenTelemetry tracer setup utilities."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter


@dataclass(slots=True)
class SpanTimer:
    start: float
    first_token_at: float | None = None

    def mark_first_token(self) -> None:
        if self.first_token_at is None:
            self.first_token_at = perf_counter()

    def ttft_ms(self) -> float:
        if self.first_token_at is None:
            return 0.0
        return (self.first_token_at - self.start) * 1000

    def total_ms(self) -> float:
        return (perf_counter() - self.start) * 1000


def start_span_timer() -> SpanTimer:
    return SpanTimer(start=perf_counter())
