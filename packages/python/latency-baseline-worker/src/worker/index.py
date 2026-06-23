import asyncio
import uvicorn
from api.rest.v1.app import app
from temporalio.client import Client
from temporalio.worker import Worker
from worker.config import load_config
from worker.activities import LatencyBaselineActivities
from worker.workflows import LatencyBaselineWorkflow
from infra.adapters.clickhouse.clickhouse_adapter import ClickHouseAdapter
from infra.adapters.redis.redis_adapter import RedisAdapter
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
    kafka_producer = ConfluentKafkaProducerAdapter(bootstrap_servers=config.kafka_bootstrap_servers)

    activities = LatencyBaselineActivities(
        clickhouse=clickhouse,
        redis=redis,
        kafka=kafka_producer
    )

    client = await Client.connect(
        config.temporal_host,
        namespace=config.temporal_namespace,
        interceptors=[TracingInterceptor()],
    )

    worker = Worker(
        client,
        task_queue=config.temporal_task_queue,
        workflows=[LatencyBaselineWorkflow],
        activities=[
            activities.hourly_checkpoint,
        ],
        interceptors=[TracingInterceptor()],
    )

    server_config = uvicorn.Config(app, host="0.0.0.0", port=config.health_port, log_level="info")
    server = uvicorn.Server(server_config)

    await asyncio.gather(
        worker.run(),
        server.serve(),
    )

if __name__ == "__main__":
    asyncio.run(main())
