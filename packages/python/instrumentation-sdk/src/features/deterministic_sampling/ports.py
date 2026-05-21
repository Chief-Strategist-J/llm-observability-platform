from typing import Protocol, Any

class SamplingGatePort(Protocol):
    def should_sample(self, span_id: Any) -> bool:
        pass
