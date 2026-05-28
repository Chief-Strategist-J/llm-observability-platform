from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class EventHandlerDefinition:
    topic: str
    handler: Callable

def build_registry(budget_handler: Callable, cost_anomaly_handler: Callable) -> dict[str, EventHandlerDefinition]:
    return {
        "alerts.budget": EventHandlerDefinition(
            topic="alerts.budget",
            handler=budget_handler,
        ),
        "alerts.cost.anomaly": EventHandlerDefinition(
            topic="alerts.cost.anomaly",
            handler=cost_anomaly_handler,
        ),
    }
