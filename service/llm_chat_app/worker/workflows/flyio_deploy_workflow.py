import logging
from datetime import timedelta
from typing import Any, Dict

from temporalio import workflow
from temporalio.common import RetryPolicy

from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

logger = logging.getLogger(__name__)


@workflow.defn
class FlyioDeploymentWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        timeout = timedelta(minutes=15)
        p = dict(params)
        p.setdefault("service_name", "flyio-deploy")

        logger.info("workflow FlyioDeploymentWorkflow start params=%s", p)

        await workflow.execute_activity(
            "generate_deployment_configs_activity",
            {**p, "platforms": ["flyio"]},
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "create_flyio_app_activity",
            p,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "set_flyio_secrets_activity",
            p,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        deploy_result = await workflow.execute_activity(
            "deploy_to_flyio_activity",
            p,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        deployment_url = None
        if isinstance(deploy_result, dict):
            deployment_url = deploy_result.get("deployment_url")

        if not deployment_url:
            app_name = p.get("app_name", "llm-chat-app")
            deployment_url = f"https://{app_name}.fly.dev"

        if deployment_url:
            await workflow.execute_activity(
                "check_deployment_health_activity",
                {**p, "url": deployment_url},
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )

        logger.info("workflow FlyioDeploymentWorkflow complete")
        return "flyio_deploy_complete"
