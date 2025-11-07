from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

@workflow.defn
class MetricsPipelineWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, service_name: str) -> str:
        await workflow.execute_activity(
            "start_prometheus_container",
            service_name,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        await workflow.execute_activity(
            "start_grafana_container",
            service_name,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        return "Metrics pipeline fully configured: Prometheus + Grafana + Dashboard"
