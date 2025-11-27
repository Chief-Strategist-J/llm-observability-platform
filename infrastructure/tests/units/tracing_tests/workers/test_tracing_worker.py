import sys
from pathlib import Path
import asyncio
from typing import Sequence, Type

root = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(root))

from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
from infrastructure.tests.units.tracing_tests.workflows.test_tracing_workflow import TestTracingWorkflow

from infrastructure.orchestrator.activities.configurations_activity.traefik_activity import (
    start_traefik_activity,
    stop_traefik_activity,
    restart_traefik_activity,
    delete_traefik_activity,
)

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
    start_opentelemetry_collector,
    stop_opentelemetry_collector,
    restart_opentelemetry_collector,
    delete_opentelemetry_collector,
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


class TestTracingWorker(BaseWorker):
    @property
    def workflows(self) -> Sequence[Type]:
        return [TestTracingWorkflow]

    @property
    def activities(self) -> Sequence[object]:
        return [
            start_traefik_activity,
            stop_traefik_activity,
            restart_traefik_activity,
            delete_traefik_activity,
 
            start_grafana_activity,
            stop_grafana_activity,
            restart_grafana_activity,
            delete_grafana_activity,

            start_tempo_activity,
            stop_tempo_activity,
            restart_tempo_activity,
            delete_tempo_activity,

            start_opentelemetry_collector,
            stop_opentelemetry_collector,
            restart_opentelemetry_collector,
            delete_opentelemetry_collector,

            # Tracing pipeline activities
            generate_config_tracings,
            configure_source_paths_tracings,
            configure_source_tracings,
            deploy_processor_tracings,
            restart_source_tracings,
            emit_test_event_tracings,
            verify_event_ingestion_tracings,
            create_grafana_datasource_tracings_activity,
        ]


if __name__ == "__main__":
    cfg = WorkerConfig(
        host="localhost",
        port=7233,
        queue="test-tracing-queue",
        namespace="default",
        max_concurrency=10,
    )
    worker = TestTracingWorker(cfg)
    asyncio.run(worker.run())
