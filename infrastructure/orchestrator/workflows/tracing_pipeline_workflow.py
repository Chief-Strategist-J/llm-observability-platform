"""Tracing Pipeline Workflow.

Defines the workflow for executing tracing pipeline activities. Manages Grafana + Jaeger
stack for distributed tracing and visualization.

"""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class TracingPipelineWorkflow:
    """Defines the workflow for executing tracing pipeline activities.

    Starts Jaeger and Grafana with proper dashboard configuration.

    """

    @workflow.run
    async def run(self, service_name: str) -> str:
        """Executes the tracing pipeline workflow in proper order.

        Order:
        1. Start Jaeger (distributed tracing backend)
        2. Start Grafana (visualization dashboard)

        """
        # Start Jaeger first
        await workflow.execute_activity(
            "start_jaeger_container",
            service_name,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        # Start Grafana for visualization
        await workflow.execute_activity(
            "start_grafana_container",
            service_name,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        return "Tracing pipeline fully configured: Jaeger + Grafana + Dashboard"
