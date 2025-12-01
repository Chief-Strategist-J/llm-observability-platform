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
from infrastructure.observability.workflows.metrics_pipeline_workflow import MetricsPipelineWorkflow
from infrastructure.observability.config.observability_config import get_observability_config

logger = logging.getLogger("metrics_pipeline_trigger")

class MetricsPipelineTrigger(BaseTrigger):
    def get_workflows(self):
        return []

    def get_activities(self):
        return []

    async def trigger_with_config(self, params: dict | None = None) -> str | None:
        client = None
        try:
            client = await Client.connect(self.host)
            workflow_id = f"{self.service_name.replace('-', '_')}_{int(time.time())}"
            workflow_params = {**self.params, **(params or {})}
            if "service_name" not in workflow_params:
                workflow_params["service_name"] = self.service_name
            config = get_observability_config()
            result = await client.start_workflow(
                MetricsPipelineWorkflow.run,
                args=[workflow_params, config.to_workflow_params()],
                id=workflow_id,
                task_queue=self.task_queue,
            )
            logger.info({
                "event": "workflow_started",
                "workflow_id": result.id,
                "service": self.service_name,
                "workflow_name": self.workflow_name,
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
    trigger = MetricsPipelineTrigger(
        host="localhost:7233",
        namespace="default",
        task_queue="metrics-pipeline-queue",
        service_name="metrics-pipeline",
        workflow_name="MetricsPipelineWorkflow",
        params={"service_name": "metrics-pipeline"},
    )
    workflow_id = asyncio.run(trigger.trigger_with_config())
    logger.info({
        "event": "trigger_complete",
        "workflow_id": workflow_id,
        "service": "metrics-pipeline",
        "timestamp": int(time.time())
    })
