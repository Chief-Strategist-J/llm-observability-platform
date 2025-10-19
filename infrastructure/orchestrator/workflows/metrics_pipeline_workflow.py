"""Metrics Pipeline Workflow.

Defines the workflow for executing metrics pipeline activities. Manages Grafana +
Prometheus stack for metrics collection and visualization.

"""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class MetricsPipelineWorkflow:
    """Defines the workflow for executing metrics pipeline activities.

    Starts Prometheus and Grafana with proper dashboard configuration.

    """

    @workflow.run
    async def run(self, service_name: str) -> str:
        """Executes the metrics pipeline workflow in proper order.

        Order:
        1. Start Prometheus (metrics collection and storage)
        2. Start Grafana (visualization dashboard)

        """
        # Start Prometheus first
        await workflow.execute_activity(
            "start_prometheus_container",
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

        return "Metrics pipeline fully configured: Prometheus + Grafana + Dashboard"
