from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

@workflow.defn
class LogsPipelineWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: dict) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        timeout = timedelta(minutes=5)

        await workflow.execute_activity(
            "stop_opentelemetry_collector",
            params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "delete_opentelemetry_collector",
            params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "start_opentelemetry_collector",
            params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "start_loki_activity",
            params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "start_grafana_activity",
            params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        return "Logs pipeline fully configured"
