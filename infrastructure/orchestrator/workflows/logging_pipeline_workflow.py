"""Logging Pipeline Workflow.

Defines the workflow for executing logging pipeline activities.

"""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class LoggingPipelineWorkflow:
    """Workflow for executing logging pipeline activities.

    Handles container startup activities with proper retry policies and timeouts.

    """

    @workflow.run
    async def run(self, service_name: str) -> str:
        """Execute the logging pipeline workflow.

        Args:
            service_name: Name of the service to start in the container.

        Returns:
            Result of the container startup activity execution.

        """
        # Dynamic import ensures non-deterministic modules are never loaded at top-level
        from infrastructure.orchestrator.activities import start_app_container

        return await workflow.execute_activity(
            start_app_container,
            service_name,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=1),
        )
