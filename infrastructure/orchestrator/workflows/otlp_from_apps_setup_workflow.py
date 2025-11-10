from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

@workflow.defn
class OtlpFromAppsSetupWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, template_path: str, service_name: str, otlp_endpoint: str) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        t = timedelta(minutes=5)

        config_path = await workflow.execute_activity(
            "enable_otlp_receiver_activity",
            template_path,
            service_name,
            otlp_endpoint,
            start_to_close_timeout=t,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "collect_and_route_otlp_activity",
            config_path,
            start_to_close_timeout=t,
            retry_policy=rp,
        )

        return "otlp_from_apps ingest enabled"
