import asyncio
import logging
from datetime import timedelta
import uvicorn
from api.rest.v1.app import app
from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleIntervalSpec,
    ScheduleSpec,
)
from temporalio.worker import Worker
from worker.config import load_config
from worker.activities import SloBurnActivities
from worker.workflows import SloBurnWorkflow
from infra.adapters.clickhouse.clickhouse_adapter import ClickHouseAdapter
from infra.adapters.redis.redis_adapter import RedisAdapter
from infra.adapters.kafka.kafka_alert_adapter import KafkaAlertAdapter
from infra.adapters.metrics.prometheus_adapter import PrometheusAdapter
from temporalio.contrib.opentelemetry import TracingInterceptor

from shared.tracing.tracer import init_tracer

init_tracer()

logger = logging.getLogger(__name__)

async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = load_config()

    clickhouse = ClickHouseAdapter(
        host=config.clickhouse_host,
        port=config.clickhouse_port,
        username=config.clickhouse_username,
        password=config.clickhouse_password,
        database=config.clickhouse_database,
    )

    redis = RedisAdapter(url=config.redis_url)
    kafka = KafkaAlertAdapter(bootstrap_servers=config.kafka_bootstrap_servers)
    metrics = PrometheusAdapter()

    activities = SloBurnActivities(
        redis=redis,
        clickhouse=clickhouse,
        kafka=kafka,
        metrics=metrics,
        slo_compliance_config_path=config.slo_compliance_config_path,
        default_slo_compliance=config.default_slo_compliance,
    )

    client = await Client.connect(
        config.temporal_host,
        namespace=config.temporal_namespace,
        interceptors=[TracingInterceptor()],
    )

    worker = Worker(
        client,
        task_queue=config.temporal_task_queue,
        workflows=[SloBurnWorkflow],
        activities=[
            activities.fetch_active_pairs,
            activities.compute_burn_rates,
            activities.write_burn_rates,
            activities.handle_alerts,
        ],
        interceptors=[TracingInterceptor()],
    )

    # Register interval schedule for every 60 seconds
    try:
        await client.create_schedule(
            "slo-burn-rate-schedule",
            Schedule(
                action=ScheduleActionStartWorkflow(
                    "SloBurnWorkflow",
                    id="slo-burn-workflow",
                    task_queue=config.temporal_task_queue,
                ),
                spec=ScheduleSpec(
                    intervals=[ScheduleIntervalSpec(every=timedelta(seconds=60))]
                ),
            ),
        )
        logger.info("Successfully created slo-burn-rate-schedule (every 60s)")
    except Exception as e:
        logger.info("slo-burn-rate-schedule already registered or failed to register: %s", e)

    server_config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(server_config)

    await asyncio.gather(
        worker.run(),
        server.serve(),
    )


if __name__ == "__main__":
    asyncio.run(main())
