import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow


@workflow.defn(name="ServiceRoutingSetupWorkflow")
class ServiceRoutingSetupWorkflow(BaseWorkflow):

    @workflow.run
    async def run(self, params: dict) -> dict:
        if not params or not isinstance(params, dict):
            return {"success": False, "error": "Invalid params provided"}

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )

        timeout = timedelta(minutes=5)

        try:
            hostnames_result = await workflow.execute_activity(
                "discover_service_hostnames_activity",
                {},
                start_to_close_timeout=timeout,
                retry_policy=retry_policy,
            )
            
            if not hostnames_result.get("success"):
                return {"success": False, "error": "Failed to discover hostnames"}

            await workflow.sleep(1)

            hosts_result = await workflow.execute_activity(
                "configure_etc_hosts_activity",
                {"hostnames": hostnames_result["hostnames"]},
                start_to_close_timeout=timeout,
                retry_policy=retry_policy,
            )
            
            if not hosts_result.get("success"):
                return {"success": False, "error": "Failed to configure /etc/hosts"}

            return {
                "success": True,
                "configured_hostnames": hostnames_result["hostnames"],
                "total_services": len(hostnames_result.get("service_names", [])),
                "backup_path": hosts_result.get("backup_path")
            }

        except Exception as e:
            return {"success": False, "error": f"Workflow failed: {str(e)}"}
