import asyncio
from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
from infrastructure.orchestrator.activities.configurations_activity.prometheus_activity import (
    start_prometheus_activity,
    stop_prometheus_activity,
    restart_prometheus_activity,
    delete_prometheus_activity,
)
from infrastructure.orchestrator.activities.configurations_activity.grafana_activity import (
    start_grafana_activity,
    stop_grafana_activity,
    restart_grafana_activity,
    delete_grafana_activity,
)
from infrastructure.orchestrator.workflows.metrics_pipeline_workflow import (
    MetricsPipelineWorkflow,
)

class MetricsPipelineWorker(BaseWorker):
    @property
    def workflows(self):
        return [MetricsPipelineWorkflow]

    @property
    def activities(self):
        return [
            start_prometheus_activity,
            stop_prometheus_activity,
            restart_prometheus_activity,
            delete_prometheus_activity,
            start_grafana_activity,
            stop_grafana_activity,
            restart_grafana_activity,
            delete_grafana_activity,
        ]

async def main():
    worker = MetricsPipelineWorker(
        WorkerConfig(
            host="localhost",
            queue="metrics-pipeline-queue",
            port=7233,
            namespace="default",
            max_concurrency=None,
        )
    )
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
