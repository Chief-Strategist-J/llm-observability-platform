import asyncio
import uvicorn
from api.rest.v1.app import app
from temporalio.client import Client
from temporalio.worker import Worker
from worker.config import load_config
from worker.activities import EwmaActivities
from worker.workflows import EwmaBaselineUpdate
from infra.adapters.clickhouse.clickhouse_adapter import ClickHouseAdapter
from infra.adapters.redis.redis_adapter import RedisAdapter
from infra.adapters.postgres.postgres_adapter import PostgresAdapter
from infra.adapters.kafka.kafka_alert_adapter import KafkaAlertAdapter


async def main() -> None:
    config = load_config()

    clickhouse = ClickHouseAdapter(
        host=config.clickhouse_host,
        port=config.clickhouse_port,
        username=config.clickhouse_username,
        password=config.clickhouse_password,
        database=config.clickhouse_database,
    )

    redis = RedisAdapter(url=config.redis_url)
    postgres = PostgresAdapter(dsn=config.postgres_dsn)
    alert_publisher = KafkaAlertAdapter(
        bootstrap_servers=config.kafka_bootstrap_servers
    )

    activities = EwmaActivities(
        clickhouse=clickhouse,
        redis=redis,
        postgres=postgres,
        alert_publisher=alert_publisher,
    )

    client = await Client.connect(
        config.temporal_host, namespace=config.temporal_namespace
    )

    worker = Worker(
        client,
        task_queue=config.temporal_task_queue,
        workflows=[EwmaBaselineUpdate],
        activities=[
            activities.fetch_active_pairs,
            activities.fetch_cost_history,
            activities.fetch_global_model_avg,
            activities.fetch_current_cost_1h,
            activities.fetch_cost_by_cluster_1h,
            activities.get_baseline,
            activities.upsert_baseline,
            activities.publish_anomaly_alert,
        ],
    )

    server_config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(server_config)

    await asyncio.gather(
        worker.run(),
        server.serve(),
    )


if __name__ == "__main__":
    asyncio.run(main())
