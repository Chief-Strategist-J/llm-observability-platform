import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.append(str(root))

import asyncio
from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
from infrastructure.observability.workflows.tracing_pipeline_workflow import TracingPipelineWorkflow

# Container management activities
from infrastructure.orchestrator.activities.configurations_activity.grafana_activity import (
    start_grafana_activity,
    stop_grafana_activity,
    restart_grafana_activity,
    delete_grafana_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.tempo_activity import (
    start_tempo_activity,
    stop_tempo_activity,
    restart_tempo_activity,
    delete_tempo_activity,
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

# Tracing pipeline activities
from infrastructure.observability.activities.tracing.exporters.tempo_exporter_activity import (
    tempo_exporter_activity,
)
from infrastructure.observability.activities.tracing.processors.span_processor_activity import (
    span_processor_activity,
)
from infrastructure.observability.activities.tracing.providers.otlp_provider_activity import (
    otlp_provider_activity,
)

from infrastructure.observability.activities.tracing.generate_config_tracings import (
    generate_config_tracings,
)
from infrastructure.observability.activities.tracing.configure_source_paths_tracings import (
    configure_source_paths_tracings,
)
from infrastructure.observability.activities.tracing.configure_source_tracings import (
    configure_source_tracings,
)
from infrastructure.observability.activities.tracing.deploy_processor_tracings import (
    deploy_processor_tracings,
)
from infrastructure.observability.activities.tracing.restart_source_tracings import (
    restart_source_tracings,
)
from infrastructure.observability.activities.tracing.emit_test_event_tracings import (
    emit_test_event_tracings,
)
from infrastructure.observability.activities.tracing.verify_event_ingestion_tracings import (
    verify_event_ingestion_tracings,
)
from infrastructure.observability.activities.tracing.create_grafana_datasource_tracings_activity import (
    create_grafana_datasource_tracings_activity,
)


class TracingPipelineWorker(BaseWorker):

    @property
    def workflows(self):
        return [TracingPipelineWorkflow]

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
            start_tempo_activity,
            stop_tempo_activity,
            restart_tempo_activity,
            delete_tempo_activity,
            start_otel_collector_activity,
            stop_otel_collector_activity,
            restart_otel_collector_activity,
            delete_otel_collector_activity,
            # Tracing pipeline
            otlp_provider_activity,
            span_processor_activity,
            tempo_exporter_activity,
            generate_config_tracings,
            configure_source_paths_tracings,
            configure_source_tracings,
            deploy_processor_tracings,
            restart_source_tracings,
            emit_test_event_tracings,
            verify_event_ingestion_tracings,
            create_grafana_datasource_tracings_activity
        ]


async def main():
    cfg = WorkerConfig(
        host="localhost",
        port=7233,
        queue="tracing-pipeline-queue",
        namespace="default",
        max_concurrency=10,
    )
    worker = TracingPipelineWorker(cfg)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
