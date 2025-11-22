from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
import logging

logger = logging.getLogger(__name__)


@workflow.defn
class ArgoCDGitOpsWorkflow:
    @workflow.run
    async def run(self, params: dict) -> str:
        """
        ArgoCD GitOps Workflow
        
        Steps:
        1. Start ArgoCD Repo Server
        2. Start ArgoCD Server
        3. Login to ArgoCD
        4. Create/Update Application
        5. Sync Application (deploy)
        6. Get deployment status
        """
        from infrastructure.orchestrator.activities.configurations_activity.argocd_activity import (
            start_argocd_repo_server_activity,
            start_argocd_server_activity,
            argocd_login_activity,
            argocd_create_application_activity,
            argocd_sync_application_activity,
            argocd_get_app_status_activity,
        )
        
        service_name = params.get("service_name", "argocd-gitops")
        app_config = params.get("app_config")
        
        if not app_config:
            return "Error: app_config is required"
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        
        timeout = timedelta(minutes=5)
        
        logger.info(f"Starting ArgoCD GitOps workflow for service: {service_name}")
        
        # Step 1: Start Repo Server
        await workflow.execute_activity(
            start_argocd_repo_server_activity,
            params,
            start_to_close_timeout=timeout,
            retry_policy=retry_policy,
        )
        
        # Step 2: Start ArgoCD Server
        await workflow.execute_activity(
            start_argocd_server_activity,
            params,
            start_to_close_timeout=timeout,
            retry_policy=retry_policy,
        )
        
        # Step 3: Login
        login_result = await workflow.execute_activity(
            argocd_login_activity,
            params,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )
        
        if not login_result.get("success"):
            return f"Error: ArgoCD login failed: {login_result.get('output')}"
        
        # Step 4: Create Application
        create_result = await workflow.execute_activity(
            argocd_create_application_activity,
            params,
            start_to_close_timeout=timeout,
            retry_policy=retry_policy,
        )
        
        if not create_result.get("success"):
            return f"Error: Failed to create ArgoCD app: {create_result.get('output')}"
        
        # Step 5: Sync Application (deploy)
        sync_params = {
            **params,
            "app_name": app_config.get("name")
        }
        sync_result = await workflow.execute_activity(
            argocd_sync_application_activity,
            sync_params,
            start_to_close_timeout=timeout,
            retry_policy=retry_policy,
        )
        
        if not sync_result.get("success"):
            return f"Error: Sync failed: {sync_result.get('output')}"
        
        # Step 6: Get status
        status_result = await workflow.execute_activity(
            argocd_get_app_status_activity,
            sync_params,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )
        
        app_name = app_config.get("name")
        return f"ArgoCD deployment complete for {app_name}. Status: {status_result.get('status')}"