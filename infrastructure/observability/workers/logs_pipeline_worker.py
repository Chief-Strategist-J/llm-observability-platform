import sys
import os
from pathlib import Path


project_root = Path(__file__).resolve().parents[3]  # Go up 3 levels to reach the project root


if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import asyncio
from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
from infrastructure.observability.workflows.logs_pipeline_workflow import LogsPipelineWorkflow
from infrastructure.orchestrator.activities.common_activities.host_manage_activity import (
    add_hosts_entries_activity,
    remove_hosts_entries_activity,
    verify_hosts_entries_activity,
    restore_hosts_backup_activity,
)


from infrastructure.orchestrator.activities.configurations_activity.grafana_activity import (
    start_grafana_activity,
    stop_grafana_activity,
    restart_grafana_activity,
    delete_grafana_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.loki_activity import (
    start_loki_activity,
    stop_loki_activity,
    restart_loki_activity,
    delete_loki_activity,
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

# Log pipeline activities
from infrastructure.observability.activities.log.exporters.loki_exporter_activity import (
    loki_exporter_activity,
)
from infrastructure.observability.activities.log.processors.json_parser_activity import (
    json_parser_activity,
)
from infrastructure.observability.activities.log.providers.file_provider_activity import (
    file_provider_activity,
)

from infrastructure.observability.activities.log.generate_config_logs import (
    generate_config_logs,
)
from infrastructure.observability.activities.log.configure_source_paths_logs import (
    configure_source_paths_logs,
)
from infrastructure.observability.activities.log.configure_source_logs import (
    configure_source_logs,
)
from infrastructure.observability.activities.log.deploy_processor_logs import (
    deploy_processor_logs,
)
from infrastructure.observability.activities.log.restart_source_logs import (
    restart_source_logs,
)
from infrastructure.observability.activities.log.emit_test_event_logs import (
    emit_test_event_logs,
)
from infrastructure.observability.activities.log.verify_event_ingestion_logs import (
    verify_event_ingestion_logs,
)
from infrastructure.observability.activities.log.create_grafana_datasource_activity import (
    create_grafana_datasource_activity,
)


class LogsPipelineWorker(BaseWorker):

    @property
    def workflows(self):
        return [LogsPipelineWorkflow]

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
            start_loki_activity,
            stop_loki_activity,
            restart_loki_activity,
            delete_loki_activity,
            start_otel_collector_activity,
            stop_otel_collector_activity,
            restart_otel_collector_activity,
            delete_otel_collector_activity,
            # Log pipeline
            file_provider_activity,
            json_parser_activity,
            loki_exporter_activity,
            generate_config_logs,
            configure_source_paths_logs,
            configure_source_logs,
            deploy_processor_logs,
            restart_source_logs,
            emit_test_event_logs,
            verify_event_ingestion_logs,
            create_grafana_datasource_activity,

            add_hosts_entries_activity,
            remove_hosts_entries_activity,
            verify_hosts_entries_activity,
            restore_hosts_backup_activity,
        ]


async def main():
    cfg = WorkerConfig(
        host="localhost",
        port=7233,
        queue="logs-pipeline-queue",
        namespace="default",
        max_concurrency=10,
    )
    worker = LogsPipelineWorker(cfg)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())