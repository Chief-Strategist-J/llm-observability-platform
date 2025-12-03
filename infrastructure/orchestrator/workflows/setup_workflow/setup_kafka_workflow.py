# infrastructure/orchestrator/workflows/setup_workflow/setup_kafka_workflow.py
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow


@workflow.defn
class SetupKafkaWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: dict) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        timeout = timedelta(minutes=5)

        # Restart Traefik to ensure it picks up new configurations
        await workflow.execute_activity(
            "restart_traefik_activity",
            params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "stop_kafka_activity",
            params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )
        
        # Ensure we use port 9094 as that's where Kafka binds in this setup
        kafka_params = dict(params)
        kafka_params["broker_port"] = 9094
        
        await workflow.execute_activity(
            "start_kafka_activity",
            kafka_params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "verify_kafka_activity",
            kafka_params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "stop_kafka_ui_activity",
            params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )
        
        # Ensure Kafka UI uses port 8082
        ui_params = dict(params)
        ui_params["env_vars"] = ui_params.get("env_vars", {})
        ui_params["env_vars"]["SERVER_PORT"] = "8082"
        
        await workflow.execute_activity(
            "start_kafka_ui_activity",
            ui_params,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        return "Kafka fully configured"
