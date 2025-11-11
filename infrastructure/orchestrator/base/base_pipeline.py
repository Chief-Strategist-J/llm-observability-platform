import json
import logging
import time
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
from typing import List


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

from temporalio.client import Client

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pipeline_trigger")


class WorkflowConfig:
    DEFAULT_SERVICE_NAME = "pipeline"
    DEFAULT_WORKFLOW_NAME = "PipelineWorkflow"
    DEFAULT_TASK_QUEUE = "pipeline-queue"
    DEFAULT_TEMPORAL_HOST = "localhost:7233"
    DEFAULT_WEB_UI_URL = "http://localhost:8080"

    def __init__(
        self,
        *,
        service_name: Optional[str] = None,
        workflow_name: Optional[str] = None,
        task_queue: Optional[str] = None,
        temporal_host: Optional[str] = None,
        web_ui_url: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        self.service_name = service_name or self.DEFAULT_SERVICE_NAME
        self.workflow_name = workflow_name or self.DEFAULT_WORKFLOW_NAME
        self.task_queue = task_queue or self.DEFAULT_TASK_QUEUE
        self.temporal_host = temporal_host or self.DEFAULT_TEMPORAL_HOST
        self.web_ui_url = web_ui_url or self.DEFAULT_WEB_UI_URL

        self.params = params or {"service_name": self.service_name}


class PipelineBase(ABC):
    @abstractmethod
    async def run_pipeline(self) -> Optional[str]:
        pass


class PipelineExecutor(PipelineBase):
    def __init__(self, config: WorkflowConfig):
        self.config = config

    async def execute_workflow(self) -> Optional[str]:
        try:
            logger.info(json.dumps({
                "event": "connect",
                "service": self.config.service_name,
                "host": self.config.temporal_host,
                "ts": int(time.time())
            }))

            client = await Client.connect(self.config.temporal_host)

            workflow_id = (
                f"{self.config.service_name.replace('-', '_')}_"
                f"{int(time.time())}"
            )

            # WE ALWAYS PASS ONE SINGLE PARAM: params dict
            result = await client.start_workflow(
                self.config.workflow_name,
                self.config.params,
                id=workflow_id,
                task_queue=self.config.task_queue,
            )

            logger.info(json.dumps({
                "event": "workflow_started",
                "workflow_id": result.id,
                "service": self.config.service_name,
                "workflow_name": self.config.workflow_name,
                "task_queue": self.config.task_queue,
                "web_ui": self.config.web_ui_url,
                "ts": int(time.time())
            }))

            return result.id

        except Exception as e:
            logger.info(json.dumps({
                "event": "workflow_start_failed",
                "service": self.config.service_name,
                "error": str(e),
                "ts": int(time.time())
            }))
            return None

    async def run_pipeline(self) -> Optional[str]:
        logger.info(json.dumps({
            "event": "pipeline_start",
            "service": self.config.service_name,
            "ts": int(time.time())
        }))

        workflow_id = await self.execute_workflow()

        if workflow_id:
            logger.info(json.dumps({
                "event": "pipeline_success",
                "workflow_id": workflow_id,
                "service": self.config.service_name,
                "ts": int(time.time())
            }))
            return workflow_id

        logger.info(json.dumps({
            "event": "pipeline_failed",
            "service": self.config.service_name,
            "ts": int(time.time())
        }))
        sys.exit(1)


class ChainedPipelineExecutor:
    def __init__(self, workflows: List[WorkflowConfig]):
        self.workflows = workflows

    async def run(self) -> Optional[str]:
        if not self.workflows:
            return None

        client = await Client.connect(self.workflows[0].temporal_host)
        result = None

        for config in self.workflows:
            workflow_id = f"{config.service_name.replace('-', '_')}_{int(time.time())}"

            handle = await client.start_workflow(
                config.workflow_name,
                config.params,
                id=workflow_id,
                task_queue=config.task_queue,
            )

            logger.info(f"[CHAIN] Started workflow: {workflow_id}")
            result = await handle.result()
            logger.info(f"[CHAIN] Completed workflow: {workflow_id} result={result}")

        return result
