import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
import time
import asyncio
from temporalio.client import Client
from infrastructure.orchestrator.base.base_trigger import BaseTrigger
from infrastructure.observability.setup.observability_stack_setup_workflow import (
    ObservabilityStackSetupWorkflow,
    ObservabilityStackTeardownWorkflow,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("observability_stack_setup_trigger")


class ObservabilityStackSetupTrigger(BaseTrigger):
    def get_workflows(self):
        return []

    def get_activities(self):
        return []

    async def trigger_setup(self, params: dict = None) -> str:
        client = None
        try:
            client = await Client.connect(self.host)
            workflow_id = f"observability_stack_setup_{int(time.time())}"
            workflow_params = {**self.params, **(params or {})}
            if "service_name" not in workflow_params:
                workflow_params["service_name"] = self.service_name
            
            result = await client.start_workflow(
                ObservabilityStackSetupWorkflow.run,
                args=[workflow_params],
                id=workflow_id,
                task_queue=self.task_queue,
            )
            
            logger.info({
                "event": "workflow_started",
                "workflow_id": result.id,
                "service": self.service_name,
                "workflow_name": "ObservabilityStackSetupWorkflow",
                "task_queue": self.task_queue,
                "ts": int(time.time())
            })
            
            return result.id
        except Exception as e:
            logger.error({
                "event": "workflow_start_failed",
                "service": self.service_name,
                "error": str(e),
                "ts": int(time.time())
            })
            return None
        finally:
            if client and hasattr(client, "close"):
                try:
                    await client.close()
                except Exception:
                    pass

    async def trigger_teardown(self, params: dict = None) -> str:
        client = None
        try:
            client = await Client.connect(self.host)
            workflow_id = f"observability_stack_teardown_{int(time.time())}"
            workflow_params = {**self.params, **(params or {})}
            
            result = await client.start_workflow(
                ObservabilityStackTeardownWorkflow.run,
                args=[workflow_params],
                id=workflow_id,
                task_queue=self.task_queue,
            )
            
            logger.info({
                "event": "workflow_started",
                "workflow_id": result.id,
                "service": self.service_name,
                "workflow_name": "ObservabilityStackTeardownWorkflow",
                "task_queue": self.task_queue,
                "ts": int(time.time())
            })
            
            return result.id
        except Exception as e:
            logger.error({
                "event": "workflow_start_failed",
                "service": self.service_name,
                "error": str(e),
                "ts": int(time.time())
            })
            return None
        finally:
            if client and hasattr(client, "close"):
                try:
                    await client.close()
                except Exception:
                    pass


if __name__ == "__main__":
    trigger = ObservabilityStackSetupTrigger(
        host="localhost:7233",
        namespace="default",
        task_queue="observability-stack-setup-queue",
        service_name="observability-stack-setup",
        workflow_name="ObservabilityStackSetupWorkflow",
        params={"service_name": "observability-stack-setup"},
    )
    
    action = sys.argv[1] if len(sys.argv) > 1 else "setup"
    
    if action == "setup":
        workflow_id = asyncio.run(trigger.trigger_setup())
    elif action == "teardown":
        workflow_id = asyncio.run(trigger.trigger_teardown())
    else:
        print(f"Unknown action: {action}. Use 'setup' or 'teardown'")
        sys.exit(1)
    
    logger.info({
        "event": "trigger_complete",
        "workflow_id": workflow_id,
        "action": action,
        "service": "observability-stack-setup",
        "timestamp": int(time.time())
    })
