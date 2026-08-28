from dataclasses import dataclass
from shared.contracts.validator import load_workflow_contracts
from worker.workflows import LatencyBaselineWorkflow

@dataclass(frozen=True)
class WorkflowDefinition:
    name: str
    handler: type
    contract: dict

def build_registry() -> dict[str, WorkflowDefinition]:
    contracts = load_workflow_contracts()
    return {
        "latency_baseline": WorkflowDefinition(
            name="LatencyBaselineWorkflow", 
            handler=LatencyBaselineWorkflow, 
            contract=contracts["latency_baseline"]
        )
    }

WORKFLOW_REGISTRY = build_registry()
