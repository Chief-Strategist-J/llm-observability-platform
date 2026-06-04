from __future__ import annotations
from temporalio.client import Client
from shared.ports.temporal_trigger_port import TemporalTriggerPort
import time


class TemporalClientAdapter(TemporalTriggerPort):
    """
    Triggers quality_score_workflow on the Temporal server.
    Workflow ID is deterministic from span_id to ensure idempotency.
    """

    def __init__(self, client: Client, task_queue: str) -> None:
        self._client = client
        self._task_queue = task_queue

    async def trigger_quality_score_workflow(
        self, span_id: str, payload: dict
    ) -> str:
        workflow_id = f"quality-score-{span_id}"
        handle = await self._client.start_workflow(
            "quality_score_workflow",
            payload,
            id=workflow_id,
            task_queue=self._task_queue,
        )
        return workflow_id
