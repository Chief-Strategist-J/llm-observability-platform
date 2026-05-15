"""Job registry for the queue worker with strict contract validation."""

from dataclasses import dataclass
import inspect
from typing import Callable

from features.enrich_span.index import enrich_span
from shared.contracts.validator import load_enrich_span_contract


@dataclass(frozen=True)
class JobDefinition:
    name: str
    handler: Callable
    contract: dict



def _validate_handler(handler: Callable) -> None:
    sig = inspect.signature(handler)
    params = sig.parameters
    if "payload" not in params or "dimensions" not in params:
        raise ValueError("Handler must accept payload and dimensions")


def build_registry() -> dict[str, JobDefinition]:
    contract = load_enrich_span_contract()
    _validate_handler(enrich_span)
    return {
        "enrich-span": JobDefinition(
            name="enrich-span",
            handler=enrich_span,
            contract=contract,
        )
    }


JOB_REGISTRY = build_registry()
