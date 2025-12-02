# infrastructure/orchestrator/workers/service_setup_worker.py
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import asyncio

from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
from infrastructure.orchestrator.activities.configurations_activity.mongodb_activity import (
    start_mongodb_activity,
    stop_mongodb_activity,
    restart_mongodb_activity,
    delete_mongodb_activity,
)
from infrastructure.orchestrator.activities.configurations_activity.traefik_activity import (
    start_traefik_activity,
    stop_traefik_activity,
    restart_traefik_activity,
    delete_traefik_activity,
)
from infrastructure.orchestrator.activities.configurations_activity.kafka_activity import (
    start_kafka_activity,
    stop_kafka_activity,
    restart_kafka_activity,
    delete_kafka_activity,
)
from infrastructure.orchestrator.activities.configurations_activity.mongo_express_activity import (
    start_mongoexpress_activity,
    stop_mongoexpress_activity,
    restart_mongoexpress_activity,
    delete_mongoexpress_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.grafana_activity import (
    start_grafana_activity,
    stop_grafana_activity,
    restart_grafana_activity,
    delete_grafana_activity,
)
from infrastructure.orchestrator.activities.configurations_activity.kafka_ui_activity import (
    start_kafka_ui_activity,
    stop_kafka_ui_activity,
    restart_kafka_ui_activity,
    delete_kafka_ui_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.loki_activity import (
    start_loki_activity,
    stop_loki_activity,
    restart_loki_activity,
    delete_loki_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.inngest_activity import (
    start_inngest_activity,
    stop_inngest_activity,
    restart_inngest_activity,
    delete_inngest_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.jaeger_activity import (
    start_jaeger_activity,
    stop_jaeger_activity,
    restart_jaeger_activity,
    delete_jaeger_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.neo4j_activity import (
    start_neo4j_activity,
    stop_neo4j_activity,
    restart_neo4j_activity,
    delete_neo4j_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.opentelemetry_collector import (
    start_otel_collector_activity,
    stop_otel_collector_activity,
    restart_otel_collector_activity,
    delete_otel_collector_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.prometheus_activity import (
    start_prometheus_activity,
    stop_prometheus_activity,
    restart_prometheus_activity,
    delete_prometheus_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.qdrant_activity import (
    start_qdrant_activity,
    stop_qdrant_activity,
    restart_qdrant_activity,
    delete_qdrant_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.alertmanager_activity import (
    start_alertmanager_activity,
    stop_alertmanager_activity,
    restart_alertmanager_activity,
    delete_alertmanager_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.promtail_activity import (
    start_promtail_activity,
    stop_promtail_activity,
    restart_promtail_activity,
    delete_promtail_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.redis_activity import (
    start_redis_activity,
    stop_redis_activity,
    restart_redis_activity,
    delete_redis_activity,
)

from infrastructure.orchestrator.activities.configurations_activity.tempo_activity import (
    start_tempo_activity,
    stop_tempo_activity,
    restart_tempo_activity,
    delete_tempo_activity,
)


from infrastructure.orchestrator.workflows.setup_workflow.setup_traefik_workflow import (
    SetupTraefikWorkflow,
)
from infrastructure.orchestrator.workflows.setup_workflow.setup_kafka_workflow import (
    SetupKafkaWorkflow,
)
from infrastructure.orchestrator.workflows.setup_workflow.setup_mongodb_workflow import (
    SetupMongoDBWorkflow,
)
from infrastructure.orchestrator.workflows.setup_workflow.setup_grafana_workflow import (
    SetupGrafanaWorkflow,
)
from infrastructure.orchestrator.workflows.setup_workflow.setup_inngest_workflow import (
    SetupInngestWorkflow,
)
from infrastructure.orchestrator.workflows.setup_workflow.setup_jaeger_workflow import (
    SetupJaegerWorkflow,
)
from infrastructure.orchestrator.workflows.setup_workflow.setup_neo4j_workflow import (
    SetupNeo4jWorkflow,
)
from infrastructure.orchestrator.workflows.setup_workflow.setup_otel_collector_workflow import (
    SetupOtelCollectorWorkflow,
)
from infrastructure.orchestrator.workflows.setup_workflow.setup_prometheus_workflow import (
    SetupPrometheusWorkflow,
)

from infrastructure.orchestrator.workflows.setup_workflow.setup_qdrant_workflow import (
    SetupQdrantWorkflow
)
from infrastructure.orchestrator.workflows.setup_workflow.setup_alertmanager_workflow import (
    SetupAlertManagerWorkflow
)
from infrastructure.orchestrator.workflows.setup_workflow.setup_promtail_workflow import (
    SetupPromtailWorkflow
)
from infrastructure.orchestrator.workflows.setup_workflow.setup_redis_workflow import (
    SetupRedisWorkflow
)
from infrastructure.orchestrator.workflows.setup_workflow.setup_tempo_workflow import (
    SetupTempoWorkflow
)

class ServiceSetupWorker(BaseWorker):
    @property
    def workflows(self):
        return [
            SetupTraefikWorkflow,
            SetupMongoDBWorkflow,
            SetupKafkaWorkflow,
            SetupGrafanaWorkflow,
            SetupInngestWorkflow,
            SetupJaegerWorkflow,
            SetupNeo4jWorkflow,
            SetupOtelCollectorWorkflow,
            SetupPrometheusWorkflow,
            SetupQdrantWorkflow,
            SetupAlertManagerWorkflow,
            SetupPromtailWorkflow,
            SetupRedisWorkflow,
            SetupTempoWorkflow,
        ]

    @property
    def activities(self):
        return [
            start_traefik_activity,
            stop_traefik_activity,
            restart_traefik_activity,
            delete_traefik_activity,

            start_kafka_activity,
            stop_kafka_activity,
            restart_kafka_activity,
            delete_kafka_activity,

            start_mongodb_activity,
            stop_mongodb_activity,
            restart_mongodb_activity,
            delete_mongodb_activity,
            
            start_mongoexpress_activity,
            stop_mongoexpress_activity,
            restart_mongoexpress_activity,
            delete_mongoexpress_activity,

            start_grafana_activity,
            stop_grafana_activity,
            restart_grafana_activity,
            delete_grafana_activity,

            start_kafka_ui_activity,
            stop_kafka_ui_activity,
            restart_kafka_ui_activity,
            delete_kafka_ui_activity,

            start_loki_activity,
            stop_loki_activity,
            restart_loki_activity,
            delete_loki_activity,

            start_inngest_activity,
            stop_inngest_activity,
            restart_inngest_activity,
            delete_inngest_activity,

            start_jaeger_activity,
            stop_jaeger_activity,
            restart_jaeger_activity,
            delete_jaeger_activity,

            start_neo4j_activity,
            stop_neo4j_activity,
            restart_neo4j_activity,
            delete_neo4j_activity,

            start_otel_collector_activity,
            stop_otel_collector_activity,
            restart_otel_collector_activity,
            delete_otel_collector_activity,

            start_prometheus_activity,
            stop_prometheus_activity,
            restart_prometheus_activity,
            delete_prometheus_activity,

            start_qdrant_activity,
            stop_qdrant_activity,
            restart_qdrant_activity,
            delete_qdrant_activity,

            start_alertmanager_activity,
            stop_alertmanager_activity,
            restart_alertmanager_activity,
            delete_alertmanager_activity,

            start_promtail_activity,
            stop_promtail_activity,
            restart_promtail_activity,
            delete_promtail_activity,

            start_redis_activity,
            stop_redis_activity,
            restart_redis_activity,
            delete_redis_activity,

            start_tempo_activity,
            stop_tempo_activity,
            restart_tempo_activity,
            delete_tempo_activity,
        ]

async def main():
    
    worker = ServiceSetupWorker(
        WorkerConfig(
            host="localhost",
            queue="service_setup_queue",
            port=7233,
            namespace="default",
            max_concurrency=None,
        )
    )

    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())

