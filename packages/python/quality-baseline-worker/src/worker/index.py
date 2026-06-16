import asyncio
import uvicorn
from api.rest.v1.app import app
from temporalio.client import Client
from temporalio.worker import Worker
from worker.config import load_config
from worker.activities import QualityBaselineActivities
from worker.workflows import RecomputeQualityBaseline, RollupQualityTrend, QualityScoreWorkflow
from infra.adapters.clickhouse.clickhouse_adapter import ClickHouseAdapter
from infra.adapters.redis.redis_adapter import RedisAdapter
from infra.adapters.postgres.postgres_adapter import PostgresAdapter
from infra.adapters.metrics.prometheus_adapter import PrometheusAdapter
from infra.adapters.scorers.http_scorer_client_adapter import HttpScorerClientAdapter
from infra.adapters.kafka.confluent_producer_adapter import ConfluentKafkaProducerAdapter

from temporalio.contrib.opentelemetry import TracingInterceptor

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
    scorer_client = HttpScorerClientAdapter()
    kafka_producer = ConfluentKafkaProducerAdapter(bootstrap_servers=config.kafka_bootstrap_servers)

    activities = QualityBaselineActivities(
        clickhouse=clickhouse,
        redis=redis,
        postgres=postgres,
        metrics=metrics,
        scorer_client=scorer_client,
        kafka_producer=kafka_producer,
    )

    client = await Client.connect(
        config.temporal_host,
        namespace=config.temporal_namespace,
        interceptors=[TracingInterceptor()],
    )

    worker = Worker(
        client,
        task_queue=config.temporal_task_queue,
        workflows=[RecomputeQualityBaseline, RollupQualityTrend, QualityScoreWorkflow],
        activities=[
            activities.recompute_baseline_scores,
            activities.write_redis_baselines,
            activities.rollup_quality_trend,
            activities.detect_language,
            activities.detect_prompt_type,
            activities.compute_coherence,
            activities.compute_toxicity,
            activities.compute_faithfulness,
            activities.compute_perplexity,
            activities.aggregate_composite,
        ],
        interceptors=[TracingInterceptor()],
    )

    server_config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(server_config)

    await asyncio.gather(
        worker.run(),
        server.serve(),
    )

if __name__ == "__main__":
    asyncio.run(main())
