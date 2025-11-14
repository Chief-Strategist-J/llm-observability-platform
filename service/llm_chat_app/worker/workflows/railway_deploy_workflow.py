import logging
from datetime import timedelta
from typing import Any, Dict

from temporalio import workflow
from temporalio.common import RetryPolicy

from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

logger = logging.getLogger(__name__)


@workflow.defn
class RailwayDeploymentWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        timeout = timedelta(minutes=15)
        p = dict(params)
        p.setdefault("service_name", "railway-deploy")

        logger.info("workflow RailwayDeploymentWorkflow start params=%s", p)

        await workflow.execute_activity(
            "generate_deployment_configs_activity",
            {**p, "platforms": ["railway"]},
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "create_railway_project_activity",
            p,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        await workflow.execute_activity(
            "set_railway_env_vars_activity",
            p,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        deploy_result = await workflow.execute_activity(
            "deploy_to_railway_activity",
            p,
            start_to_close_timeout=timeout,
            retry_policy=rp,
        )

        deployment_url = None
        if isinstance(deploy_result, dict):
            deployment_url = deploy_result.get("deployment_url")

        if deployment_url:
            await workflow.execute_activity(
                "check_deployment_health_activity",
                {**p, "url": deployment_url},
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )

        logger.info("workflow RailwayDeploymentWorkflow complete")
        return "railway_deploy_complete"
