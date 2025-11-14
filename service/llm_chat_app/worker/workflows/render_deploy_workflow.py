import logging
from datetime import timedelta
from typing import Any, Dict

from temporalio import workflow
from temporalio.common import RetryPolicy

from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

logger = logging.getLogger(__name__)


@workflow.defn
class RenderDeploymentWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        timeout = timedelta(minutes=15)
        p = dict(params)
        p.setdefault("service_name", "render-deploy")

        logger.info("workflow RenderDeploymentWorkflow start params=%s", p)

        await workflow.execute_activity(
            "generate_deployment_configs_activity",
            {**p, "platforms": ["render"]},
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "create_render_blueprint_activity",
            p,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        push_result = await workflow.execute_activity(
            "push_to_github_activity",
            p,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "deploy_to_render_activity",
            {**p, **(push_result or {})},
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        deployment_url = None
        if isinstance(push_result, dict):
            deployment_url = push_result.get("deployment_url")
        if not deployment_url:
            deployment_url = (push_result or {}).get("repo_url")

        if deployment_url:
            await workflow.execute_activity(
                "check_deployment_health_activity",
                {**p, "url": deployment_url},
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )

        logger.info("workflow RenderDeploymentWorkflow complete")
        return "render_deploy_complete"
