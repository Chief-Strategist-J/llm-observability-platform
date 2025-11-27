import sys
from pathlib import Path
from datetime import timedelta
from typing import Dict, Any

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from temporalio import workflow
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow


@workflow.defn
class CICDPipelineWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> str:
        workflow.logger.info({
            "labels": {"pipeline": "cicd", "event": "start"},
            "msg": "workflow_start",
            "params_keys": list(params.keys())
        })

        application_name = params.get("application_name", "observability-platform")
        namespace = params.get("namespace", "argocd")
        repo_url = params.get(
            "repo_url",
            "https://github.com/Chief-Strategist-J/llm-observability-platform"
        )
        deployment_path = params.get("deployment_path", "deployments/observability")

        workflow.logger.info({
            "labels": {"pipeline": "cicd", "event": "config"},
            "msg": "deployment_config_resolved",
            "application_name": application_name,
            "namespace": namespace,
            "repo_url": repo_url,
            "deployment_path": deployment_path
        })

        deploy_res = await workflow.execute_activity(
            "deploy_to_argocd",
            {
                "application_name": application_name,
                "namespace": namespace,
                "repo_url": repo_url,
                "path": deployment_path
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "labels": {"pipeline": "cicd", "event": "deploy"},
            "msg": "argocd_deploy_completed",
            "result": deploy_res
        })

        if not deploy_res.get("success"):
            workflow.logger.error({
                "labels": {"pipeline": "cicd", "event": "deploy"},
                "msg": "argocd_deploy_failed",
                "error": deploy_res.get("error")
            })
            return "cicd_pipeline_failed"

        await workflow.sleep(5)

        sync_res = await workflow.execute_activity(
            "sync_argocd_application",
            {"application_name": application_name},
            start_to_close_timeout=timedelta(seconds=180),
        )

        workflow.logger.info({
            "labels": {"pipeline": "cicd", "event": "sync"},
            "msg": "argocd_sync_completed",
            "result": sync_res
        })

        if not sync_res.get("success"):
            workflow.logger.warning({
                "labels": {"pipeline": "cicd", "event": "sync"},
                "msg": "argocd_sync_failed",
                "error": sync_res.get("error")
            })

        status_res = await workflow.execute_activity(
            "get_argocd_app_status",
            {"application_name": application_name},
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info({
            "labels": {"pipeline": "cicd", "event": "status"},
            "msg": "argocd_status_retrieved",
            "result": status_res
        })

        workflow.logger.info({
            "labels": {"pipeline": "cicd", "event": "done"},
            "msg": "workflow_complete"
        })

        return "cicd_pipeline_completed"
