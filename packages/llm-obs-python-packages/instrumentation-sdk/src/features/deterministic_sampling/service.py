from typing import Any
from .ports import SamplingGatePort

class DeterministicSamplingService:
    def __init__(self, gate: SamplingGatePort):
        self._gate = gate

    def should_sample(self, span_id: Any) -> bool:
        return self._gate.should_sample(span_id)
