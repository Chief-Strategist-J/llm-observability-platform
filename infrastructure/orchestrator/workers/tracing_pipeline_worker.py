import asyncio
from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
from infrastructure.orchestrator.activities.configurations_activity.jaeger_activity import (
    start_jaeger_activity,
    stop_jaeger_activity,
    restart_jaeger_activity,
    delete_jaeger_activity,
)
from infrastructure.orchestrator.activities.configurations_activity.grafana_activity import (
    start_grafana_activity,
    stop_grafana_activity,
    restart_grafana_activity,
    delete_grafana_activity,
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
            start_jaeger_activity,
            stop_jaeger_activity,
            restart_jaeger_activity,
            delete_jaeger_activity,
            start_grafana_activity,
            stop_grafana_activity,
            restart_grafana_activity,
            delete_grafana_activity,
        ]

async def main():
    worker = TracingPipelineWorker(
        WorkerConfig(
            host="localhost",
            queue="tracing-pipeline-queue",
            port=7233,
            namespace="default",
            max_concurrency=None,
        )
    )
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
