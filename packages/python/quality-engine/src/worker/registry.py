from __future__ import annotations
from dataclasses import dataclass


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
