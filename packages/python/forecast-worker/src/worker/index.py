import asyncio
import uvicorn
from api.rest.v1.app import app
from temporalio.client import Client
from temporalio.worker import Worker
from worker.config import load_config
from worker.activities import ForecastActivities
from worker.workflows import ForecastWorkflow
from infra.adapters.clickhouse.clickhouse_adapter import ClickHouseAdapter
from infra.adapters.postgres.postgres_adapter import PostgresAdapter
from infra.adapters.redis.redis_adapter import RedisAdapter
from infra.adapters.kafka.kafka_alert_adapter import KafkaAlertAdapter
from infra.adapters.timesfm.timesfm_adapter import TimesFMAdapter

async def main() -> None:
    config = load_config()

    clickhouse = ClickHouseAdapter(
        host=config.clickhouse_host,
        port=config.clickhouse_port,
        username=config.clickhouse_username,
        password=config.clickhouse_password,
        database=config.clickhouse_database,
    )

    postgres = PostgresAdapter(dsn=config.postgres_dsn)
    redis = RedisAdapter(url=config.redis_url)
    alert_publisher = KafkaAlertAdapter(bootstrap_servers=config.kafka_bootstrap_servers)
    timesfm = TimesFMAdapter(repo_id=config.timesfm_repo_id, backend=config.timesfm_backend)

    activities = ForecastActivities(
        clickhouse=clickhouse,
        postgres=postgres,
        redis=redis,
        timesfm=timesfm,
        alert_publisher=alert_publisher,
        sdk_url=config.instrumentation_sdk_url
    )

    client = await Client.connect(
        config.temporal_host, namespace=config.temporal_namespace
    )

    worker = Worker(
        client,
        task_queue=config.temporal_task_queue,
        workflows=[ForecastWorkflow],
        activities=[
            activities.fetch_cost_series,
            activities.fetch_latency_series,
            activities.run_timesfm_forecast,
            activities.write_forecast_outputs,
            activities.check_predicted_breach,
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
