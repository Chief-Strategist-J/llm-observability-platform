from dataclasses import dataclass
from typing import Any
from shared.contracts.validator import load_workflow_contract
from worker.workflows import SloBurnWorkflow


@dataclass(frozen=True)
class WorkflowDefinition:
    name: str
    handler: type
    contract: dict[str, Any]


def build_registry() -> dict[str, WorkflowDefinition]:
    contract = load_workflow_contract()
    return {
        "slo_burn_computation": WorkflowDefinition(
            name="slo_burn_computation", handler=SloBurnWorkflow, contract=contract
        )
    }


WORKFLOW_REGISTRY = build_registry()
