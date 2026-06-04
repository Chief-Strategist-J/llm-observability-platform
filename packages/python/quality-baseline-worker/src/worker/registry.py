from dataclasses import dataclass
from shared.contracts.validator import load_workflow_contracts
from worker.workflows import RecomputeQualityBaseline, RollupQualityTrend

@dataclass(frozen=True)
class WorkflowDefinition:
    name: str
    handler: type
    contract: dict

def build_registry() -> dict[str, WorkflowDefinition]:
    contracts = load_workflow_contracts()
    return {
        "recompute_quality_baseline": WorkflowDefinition(
            name="recompute_quality_baseline", 
            handler=RecomputeQualityBaseline, 
            contract=contracts["recompute"]
        ),
        "rollup_quality_trend": WorkflowDefinition(
            name="rollup_quality_trend", 
            handler=RollupQualityTrend, 
            contract=contracts["rollup"]
        )
    }

WORKFLOW_REGISTRY = build_registry()
