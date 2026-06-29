from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class EventHandlerDefinition:
    topic: str
    handler: Callable

def build_registry(
    budget_handler: Callable,
    cost_anomaly_handler: Callable,
    toxicity_handler: Callable,
    degradation_handler: Callable,
    latency_slo_handler: Callable,
) -> dict[str, EventHandlerDefinition]:
    return {
        "alerts.budget": EventHandlerDefinition(
            topic="alerts.budget",
            handler=budget_handler,
        ),
        "alerts.cost.anomaly": EventHandlerDefinition(
            topic="alerts.cost.anomaly",
            handler=cost_anomaly_handler,
        ),
        "llm.toxicity.flagged": EventHandlerDefinition(
            topic="llm.toxicity.flagged",
            handler=toxicity_handler,
        ),
        "alerts.quality.degradation": EventHandlerDefinition(
            topic="alerts.quality.degradation",
            handler=degradation_handler,
        ),
        "alerts.latency.slo": EventHandlerDefinition(
            topic="alerts.latency.slo",
            handler=latency_slo_handler,
        ),
    }


