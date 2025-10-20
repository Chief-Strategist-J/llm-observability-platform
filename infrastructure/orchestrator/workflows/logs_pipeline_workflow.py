"""Logs Pipeline Workflow.

Defines the workflow for executing logs pipeline activities. Manages Grafana + Loki +
Promtail stack for log aggregation and visualization.

"""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class LogsPipelineWorkflow:
    """Defines the workflow for executing logs pipeline activities.

    Starts Loki, then Promtail, and finally Grafana with proper dashboard configuration.

    """

    @workflow.run
    async def run(self, service_name: str) -> str:
        """Executes the logs pipeline workflow in proper order.

        Order:
        1. Start Loki (log aggregation backend)
        2. Start Promtail (log shipper)
        3. Start Grafana (visualization dashboard)

        """ 
        # Start Loki first
        await workflow.execute_activity(
            "start_loki_container",
            service_name,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        # Start Promtail to ship logs to Loki
        await workflow.execute_activity(
            "start_promtail_container",
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

        await workflow.execute_activity(
            "configure_grafana",
            service_name,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        return "Logs pipeline fully configured: Loki + Promtail + Grafana + Dashboard"
