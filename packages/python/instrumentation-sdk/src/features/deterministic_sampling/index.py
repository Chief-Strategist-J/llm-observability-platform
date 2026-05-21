from typing import Any
from .service import DeterministicSamplingService
from .infra.adapters.sha256_sampling_adapter import Sha256SamplingAdapter

_GATE = Sha256SamplingAdapter()
_SERVICE = DeterministicSamplingService(_GATE)

def should_sample(span_id: Any) -> bool:
    return _SERVICE.should_sample(span_id)
