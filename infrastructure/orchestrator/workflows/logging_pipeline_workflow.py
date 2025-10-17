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
        # Execute logs-related activities SEQUENTIALLY (one at a time, step-by-step)
        # Each service must fully complete before the next starts
        workflow.logger.info("Starting Grafana container (step 1/3)...")
        await workflow.execute_activity(
            "start_grafana_container",
            service_name,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(maximum_attempts=1),
        )
        workflow.logger.info("Grafana started successfully. Now starting Loki container (step 2/3)...")
        await workflow.execute_activity(
            "start_loki_container",
            service_name,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(maximum_attempts=1),
        )
        workflow.logger.info("Loki started successfully. Now starting Promtail container (step 3/3)...")
        await workflow.execute_activity(
            "start_promtail_container",
            service_name,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(maximum_attempts=1),
        )
        workflow.logger.info("All logs-related containers started sequentially.")
        return "All logs-related containers started successfully"
