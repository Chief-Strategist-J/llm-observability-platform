import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
import time
from infrastructure.orchestrator.base.base_trigger import BaseTrigger

logger = logging.getLogger("metrics_pipeline_trigger")

class MetricsPipelineTrigger(BaseTrigger):
    def get_workflows(self):
        return []

    def get_activities(self):
        return []

if __name__ == "__main__":
    trigger = MetricsPipelineTrigger(
        host="localhost:7233",
        namespace="default",
        task_queue="metrics-pipeline-queue",
        service_name="metrics-pipeline",
        workflow_name="MetricsPipelineWorkflow",
        params={"service_name": "metrics-pipeline"},
    )
    workflow_id = trigger.run_as_trigger()
    logger.info({
        "event": "trigger_complete",
        "workflow_id": workflow_id,
        "service": "metrics-pipeline",
        "timestamp": int(time.time())
    })
