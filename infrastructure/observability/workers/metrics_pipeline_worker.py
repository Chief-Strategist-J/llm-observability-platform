import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.append(str(root))

import asyncio
from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
from infrastructure.observability.workflows.metrics_pipeline_workflow import MetricsPipelineWorkflow

# Container management activities
from infrastructure.orchestrator.activities.configurations_activity.grafana_activity import (
    start_grafana_activity,
    stop_grafana_activity,
    restart_grafana_activity,
    delete_grafana_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.prometheus_activity import (
    start_prometheus_activity,
    stop_prometheus_activity,
    restart_prometheus_activity,
    delete_prometheus_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.opentelemetry_collector import (
    start_otel_collector_activity,
    stop_otel_collector_activity,
    restart_otel_collector_activity,
    delete_otel_collector_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.traefik_activity import (
    start_traefik_activity,
    stop_traefik_activity,
    restart_traefik_activity,
    delete_traefik_activity,
)

# Metrics pipeline component activities
from infrastructure.observability.activities.metrics.exporters.prometheus_exporter_activity import (
    prometheus_exporter_activity,
)
from infrastructure.observability.activities.metrics.processors.metrics_processor_activity import (
    metrics_processor_activity,
)
from infrastructure.observability.activities.metrics.providers.prometheus_provider_activity import (
    prometheus_provider_activity,
)

# Metrics pipeline activities
from infrastructure.observability.activities.metrics.generate_config_metrics import (
    generate_config_metrics,
)
from infrastructure.observability.activities.metrics.configure_source_paths_metrics import (
    configure_source_paths_metrics,
)
from infrastructure.observability.activities.metrics.configure_source_metrics import (
    configure_source_metrics,
)
from infrastructure.observability.activities.metrics.deploy_processor_metrics import (
    deploy_processor_metrics,
)
from infrastructure.observability.activities.metrics.restart_source_metrics import (
    restart_source_metrics,
)
from infrastructure.observability.activities.metrics.emit_test_event_metrics import (
    emit_test_event_metrics,
)
from infrastructure.observability.activities.metrics.verify_event_ingestion_metrics import (
    verify_event_ingestion_metrics,
)
from infrastructure.observability.activities.metrics.create_grafana_datasource_metrics import (
    create_grafana_datasource_metrics,
)


class MetricsPipelineWorker(BaseWorker):

    @property
    def workflows(self):
        return [MetricsPipelineWorkflow]

    @property
    def activities(self):
        return [
            # Traefik (MUST be first)
            start_traefik_activity,
            stop_traefik_activity,
            restart_traefik_activity,
            delete_traefik_activity,
            # Observability stack
            start_grafana_activity,
            stop_grafana_activity,
            restart_grafana_activity,
            delete_grafana_activity,
            start_prometheus_activity,
            stop_prometheus_activity,
            restart_prometheus_activity,
            delete_prometheus_activity,
            start_otel_collector_activity,
            stop_otel_collector_activity,
            restart_otel_collector_activity,
            delete_otel_collector_activity,
            # Metrics pipeline components
            prometheus_provider_activity,
            metrics_processor_activity,
            prometheus_exporter_activity,
            # Metrics pipeline
            generate_config_metrics,
            configure_source_paths_metrics,
            configure_source_metrics,
            deploy_processor_metrics,
            restart_source_metrics,
            emit_test_event_metrics,
            verify_event_ingestion_metrics,
            create_grafana_datasource_metrics
        ]


async def main():
    cfg = WorkerConfig(
        host="localhost",
        port=7233,
        queue="metrics-pipeline-queue",
        namespace="default",
        max_concurrency=10,
    )
    worker = MetricsPipelineWorker(cfg)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
