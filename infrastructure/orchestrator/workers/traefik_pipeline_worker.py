import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import asyncio
from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
from infrastructure.orchestrator.activities.configurations_activity.traefik_activity import (
    start_traefik_activity,
    stop_traefik_activity,
    restart_traefik_activity,
    delete_traefik_activity,
)

from infrastructure.orchestrator.workflows.tracing_pipeline_workflow import (
    TracingPipelineWorkflow,
)

class TracingPipelineWorker(BaseWorker):
    @property
    def workflows(self):
        return [TracingPipelineWorkflow]

    @property
    def activities(self):
        return [
            start_traefik_activity,
            stop_traefik_activity,
            restart_traefik_activity,
            delete_traefik_activity,
        ]

async def main():
    worker = TracingPipelineWorker(
        WorkerConfig(
            host="localhost",
            queue="traefik-pipeline-queue",
            port=7233,
            namespace="default",
            max_concurrency=None,
        )
    )
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
