from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from abc import ABC, abstractmethod
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

@workflow.defn
class LogsPipelineWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, service_name: str) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        t = timedelta(minutes=5)
        await workflow.execute_activity(
            "stop_opentelemetry_collector",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "delete_opentelemetry_collector",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "start_opentelemetry_collector",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "start_loki_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "start_grafana_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )

        return "Logs pipeline fully configured"
