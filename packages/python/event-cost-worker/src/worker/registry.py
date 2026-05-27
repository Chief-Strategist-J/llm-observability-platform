from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class EventHandlerDefinition:
    topic: str
    handler: Callable


def build_registry(batch_handler: Callable) -> dict[str, EventHandlerDefinition]:
    return {
        "llm.spans.raw": EventHandlerDefinition(
            topic="llm.spans.raw",
            handler=batch_handler,
        ),
    }
