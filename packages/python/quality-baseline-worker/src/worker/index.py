import asyncio
import uvicorn
from api.rest.v1.app import app
from temporalio.client import Client
from temporalio.worker import Worker
from worker.config import load_config
from worker.activities import QualityBaselineActivities
from worker.workflows import RecomputeQualityBaseline, RollupQualityTrend
from infra.adapters.clickhouse.clickhouse_adapter import ClickHouseAdapter
from infra.adapters.redis.redis_adapter import RedisAdapter
from infra.adapters.postgres.postgres_adapter import PostgresAdapter
from infra.adapters.metrics.prometheus_adapter import PrometheusAdapter

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
    metrics = PrometheusAdapter()

    activities = QualityBaselineActivities(
        clickhouse=clickhouse,
        redis=redis,
        postgres=postgres,
        metrics=metrics,
    )

    client = await Client.connect(
        config.temporal_host, namespace=config.temporal_namespace
    )

    worker = Worker(
        client,
        task_queue=config.temporal_task_queue,
        workflows=[RecomputeQualityBaseline, RollupQualityTrend],
        activities=[
            activities.recompute_baseline_scores,
            activities.write_redis_baselines,
            activities.rollup_quality_trend,
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
