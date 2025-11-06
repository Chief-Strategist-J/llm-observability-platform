from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class LogsPipelineWorker(BaseWorker):

    @property
    def workflows(self):
        from infrastructure.orchestrator.workflows.logs_pipeline_workflow import LogsPipelineWorkflow
        return [LogsPipelineWorkflow]

    @property
    def activities(self):
        from infrastructure.orchestrator.activities.configurations_activity.loki_activity import (
            start_loki_activity, stop_loki_activity,
            restart_loki_activity, delete_loki_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.promtail_activity import (
            start_promtail_activity, stop_promtail_activity,
            restart_promtail_activity, delete_promtail_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.prometheus_activity import (
            start_prometheus_activity, stop_prometheus_activity,
            restart_prometheus_activity, delete_prometheus_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.grafana_activity import (
            start_grafana_activity, stop_grafana_activity,
            restart_grafana_activity, delete_grafana_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.jaeger_activity import (
            start_jaeger_activity, stop_jaeger_activity,
            restart_jaeger_activity, delete_jaeger_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.opentelemetry_collector import (
            start_opentelemetry_collector, stop_opentelemetry_collector,
            restart_opentelemetry_collector, delete_opentelemetry_collector,
        )
        from infrastructure.orchestrator.activities.configurations_activity.neo4j_activity import (
            start_neo4j_activity, stop_neo4j_activity,
            restart_neo4j_activity, delete_neo4j_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.qdrant_activity import (
            start_qdrant_activity, stop_qdrant_activity,
            restart_qdrant_activity, delete_qdrant_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.redis_activity import (
            start_redis_activity, stop_redis_activity,
            restart_redis_activity, delete_redis_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.kafka_activity import (
            start_kafka_activity, stop_kafka_activity,
            restart_kafka_activity, delete_kafka_activity,
        )

        return [
            start_loki_activity, stop_loki_activity,
            restart_loki_activity, delete_loki_activity,
            start_promtail_activity, stop_promtail_activity,
            restart_promtail_activity, delete_promtail_activity,
            start_prometheus_activity, stop_prometheus_activity,
            restart_prometheus_activity, delete_prometheus_activity,
            start_grafana_activity, stop_grafana_activity,
            restart_grafana_activity, delete_grafana_activity,
            start_jaeger_activity, stop_jaeger_activity,
            restart_jaeger_activity, delete_jaeger_activity,
            start_opentelemetry_collector, stop_opentelemetry_collector,
            restart_opentelemetry_collector, delete_opentelemetry_collector,
            start_neo4j_activity, stop_neo4j_activity,
            restart_neo4j_activity, delete_neo4j_activity,
            start_qdrant_activity, stop_qdrant_activity,
            restart_qdrant_activity, delete_qdrant_activity,
            start_redis_activity, stop_redis_activity,
            restart_redis_activity, delete_redis_activity,
            start_kafka_activity, stop_kafka_activity,
            restart_kafka_activity, delete_kafka_activity,
        ]


async def main() -> None:
    worker = LogsPipelineWorker(
        WorkerConfig(
            host="localhost:7233",
            queue="logs-pipeline-queue",
        )
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
