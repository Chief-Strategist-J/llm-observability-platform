from __future__ import annotations
from dataclasses import dataclass


# ── Event handler registry (Kafka consumer) ──────────────────────────────────

@dataclass(frozen=True)
class EventHandlerDefinition:
    name: str
    topic: str
    consumer_group: str
    handler_class: str


HANDLER_REGISTRY: list[EventHandlerDefinition] = [
    EventHandlerDefinition(
        name="span_quality",
        topic="llm.spans.sampled",
        consumer_group="quality-engine-group",
        handler_class="handlers.span_quality.index.SpanQualityHandler",
    ),
]


# ── Temporal workflow registry (baseline scheduler) ───────────────────────────

@dataclass(frozen=True)
class WorkflowDefinition:
    name: str
    handler: type
    contract: dict


def build_workflow_registry() -> dict[str, WorkflowDefinition]:
    from shared.contracts.validator import load_workflow_contracts
    from worker.workflows import RecomputeQualityBaseline, RollupQualityTrend, QualityScoreWorkflow

    contracts = load_workflow_contracts()
    return {
        "recompute_quality_baseline": WorkflowDefinition(
            name="recompute_quality_baseline",
            handler=RecomputeQualityBaseline,
            contract=contracts["recompute"],
        ),
        "rollup_quality_trend": WorkflowDefinition(
            name="rollup_quality_trend",
            handler=RollupQualityTrend,
            contract=contracts["rollup"],
        ),
        "quality_score_workflow": WorkflowDefinition(
            name="quality_score_workflow",
            handler=QualityScoreWorkflow,
            contract=contracts["quality_score"],
        ),
    }


WORKFLOW_REGISTRY = build_workflow_registry()
