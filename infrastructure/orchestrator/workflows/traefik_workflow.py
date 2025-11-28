import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow


@workflow.defn(name="TraefikPipelineWorkflow")
class TraefikPipelineWorkflow(BaseWorkflow):

    @workflow.run
    async def run(self, params: dict) -> str:
        if not params or not isinstance(params, dict):
            return "Error: Invalid params provided"

        service_name = params.get("service_name")
        if not service_name or not isinstance(service_name, str):
            return "Error: service_name is required and must be string"

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )

        timeout = timedelta(minutes=5)

        try:
            start_result = await workflow.execute_activity(
                "start_traefik_activity",
                params,
                start_to_close_timeout=timeout,
                retry_policy=retry_policy,
            )
            if not start_result:
                return "Error: Failed to start Traefik"

            await workflow.sleep(2)

            stop_result = await workflow.execute_activity(
                "stop_traefik_activity",
                params,
                start_to_close_timeout=timeout,
                retry_policy=retry_policy,
            )
            if not stop_result:
                return "Error: Failed to stop Traefik"

            await workflow.sleep(2)

            restart_result = await workflow.execute_activity(
                "restart_traefik_activity",
                params,
                start_to_close_timeout=timeout,
                retry_policy=retry_policy,
            )
            if not restart_result:
                return "Error: Failed to restart Traefik"

            await workflow.sleep(2)

            delete_result = await workflow.execute_activity(
                "delete_traefik_activity",
                params,
                start_to_close_timeout=timeout,
                retry_policy=retry_policy,
            )
            if not delete_result:
                return "Error: Failed to delete Traefik"

            return "Traefik pipeline executed: start → stop → restart → delete completed"

        except Exception as e:
            return f"Error: Traefik pipeline failed: {str(e)}"
