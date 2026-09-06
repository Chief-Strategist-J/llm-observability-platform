from __future__ import annotations
from typing import Protocol


class TemporalTriggerPort(Protocol):
    """Port for triggering Temporal workflows from the Kafka consumer."""

    async def trigger_quality_score_workflow(
        self,
        span_id: str,
        payload: dict,
    ) -> str:
        """Start quality_score_workflow and return the workflow_id."""
        ...
