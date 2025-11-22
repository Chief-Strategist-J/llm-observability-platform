import asyncio
import logging
import sys
from pathlib import Path
from typing import Sequence, Type

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from temporalio.client import Client
from temporalio.worker import Worker
from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
from infrastructure.orchestrator.workflows.alerting_pipeline_workflow import AlertingPipelineWorkflow
from infrastructure.orchestrator.activities.configurations_activity.alertmanager_activity import (
    start_alertmanager_activity,
    stop_alertmanager_activity,
    restart_alertmanager_activity,
    delete_alertmanager_activity,
    reload_alertmanager_config_activity,
    validate_alertmanager_config_activity,
    test_slack_integration_activity,
)
from infrastructure.orchestrator.activities.configurations_activity.prometheus_activity import (
    start_prometheus_container,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AlertingPipelineWorker(BaseWorker):
    @property
    def workflows(self) -> Sequence[Type]:
        return [AlertingPipelineWorkflow]

    @property
    def activities(self) -> Sequence[object]:
        return [
            start_alertmanager_activity,
            stop_alertmanager_activity,
            restart_alertmanager_activity,
            delete_alertmanager_activity,
            reload_alertmanager_config_activity,
            validate_alertmanager_config_activity,
            test_slack_integration_activity,
            start_prometheus_container,
        ]


async def main():
    config = WorkerConfig(
        host="localhost",
        port=7233,
        queue="alerting-pipeline-queue",
        namespace="default",
        max_concurrency=10,
    )
    
    worker = AlertingPipelineWorker(config)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())