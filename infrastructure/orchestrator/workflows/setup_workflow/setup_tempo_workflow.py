# infrastructure/orchestrator/workflows/setup_workflow/setup_traefik_workflow.py
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow


@workflow.defn
class SetupTempoWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: dict) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        timeout = timedelta(minutes=5)

        await workflow.execute_activity(
            "stop_traefik_activity",
            params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "delete_traefik_activity",
            params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "start_traefik_activity",
            params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "stop_tempo_activity",
            params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "delete_tempo_activity",
            params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "start_tempo_activity",
            params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        return "Tempo fully configured"
