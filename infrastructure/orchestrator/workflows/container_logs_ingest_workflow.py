from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

@workflow.defn
class ContainerLogsIngestWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, template_path: str, log_paths: list, service_name: str, loki_endpoint: str) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        t = timedelta(minutes=5)

        config_str = await workflow.execute_activity(
            "generate_and_validate_config_activity",
            template_path,
            log_paths,
            service_name,
            loki_endpoint,
            start_to_close_timeout=t,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "push_and_reload_activity",
            config_str,
            start_to_close_timeout=t,
            retry_policy=rp,
        )

        return "container_logs ingest configured"
