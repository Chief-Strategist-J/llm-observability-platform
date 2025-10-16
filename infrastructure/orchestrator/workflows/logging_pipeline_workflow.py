"""Package: datetime

Contains the timedelta class, which represents a duration defined by days,
hours, minutes and seconds.
"""

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.activities import start_app_container


@workflow.defn
class LoggingPipelineWorkflow:
    """Workflow for executing logging pipeline activities.

    This workflow handles the execution of container startup activities for logging
    pipeline services with proper retry policies and timeouts.

    """

    @workflow.run
    async def run(self, service_name: str) -> str:
        """Execute the logging pipeline workflow.

        Args:
            service_name: Name of the service to start in the container

        Returns:
            Result of the container startup activity execution

        """
        return await workflow.execute_activity(
            start_app_container,
            service_name,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=1),
        )
