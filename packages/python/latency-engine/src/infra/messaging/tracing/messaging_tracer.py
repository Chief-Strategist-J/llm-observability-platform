from __future__ import annotations

from typing import Any
from shared.tracing.tracer import get_tracer


class MessagingTracer:
    def __init__(self, service_name: str = "latency-engine-messaging") -> None:
        self.tracer = get_tracer()

    def start_messaging_span(self, name: str, attributes: dict[str, Any] | None = None) -> Any:
        span = self.tracer.start_span(name)
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        return span
