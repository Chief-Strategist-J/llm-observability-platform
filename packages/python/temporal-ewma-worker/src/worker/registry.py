from dataclasses import dataclass
from shared.contracts.validator import load_workflow_contract
from worker.workflows import EwmaBaselineUpdate


@dataclass(frozen=True)
class WorkflowDefinition:
    name: str
    handler: type
    contract: dict


def build_registry() -> dict[str, WorkflowDefinition]:
    contract = load_workflow_contract()
    return {
        "ewma_baseline_update": WorkflowDefinition(
            name="ewma_baseline_update", handler=EwmaBaselineUpdate, contract=contract
        )
    }


WORKFLOW_REGISTRY = build_registry()
