import asyncio
import logging
import argparse
import uuid
from temporalio.client import Client

# Workflows
from infrastructure.database.postgres.setup.postgres_setup_workflow import PostgresSetupWorkflow
from infrastructure.database.mongodb.setup.mongodb_setup_workflow import MongodbSetupWorkflow
from infrastructure.database.redis.setup.redis_setup_workflow import RedisSetupWorkflow
from infrastructure.database.neo4j.setup.neo4j_setup_workflow import Neo4jSetupWorkflow
from infrastructure.database.qdrant.setup.qdrant_setup_workflow import QdrantSetupWorkflow
from infrastructure.database.minio.setup.minio_setup_workflow import MinioSetupWorkflow
from infrastructure.database.clickhouse.setup.clickhouse_setup_workflow import ClickhouseSetupWorkflow
from infrastructure.database.opensearch.setup.opensearch_setup_workflow import OpensearchSetupWorkflow
from infrastructure.database.cassandra.setup.cassandra_setup_workflow import CassandraSetupWorkflow
from infrastructure.database.milvus.setup.milvus_setup_workflow import MilvusSetupWorkflow
from infrastructure.database.weaviate.setup.weaviate_setup_workflow import WeaviateSetupWorkflow
from infrastructure.database.chroma.setup.chroma_setup_workflow import ChromaSetupWorkflow

async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Manage Database Stack")
    available_services = [
        "postgres", "mongodb", "redis", "neo4j", "qdrant", "minio",
        "clickhouse", "opensearch", "cassandra", "milvus", "weaviate", "chroma"
    ]
    parser.add_argument("--enable", nargs="+", choices=available_services, help="Enable specific services")
    parser.add_argument("--all", action="store_true", help="Enable all services")
    args = parser.parse_args()

    services_to_enable = []
    if args.all:
        services_to_enable = available_services
    elif args.enable:
        services_to_enable = args.enable

    if not services_to_enable:
        print(f"No services selected. Use --enable [service...] or --all. Available: {available_services}")
        return

    client = await Client.connect("localhost:7233", namespace="default")

    # Helper to trigger workflow
    async def trigger(name, workflow_cls, base_id):
        if name in services_to_enable:
            logger.info(f"Triggering {name.capitalize()} Setup...")
            # Append UUID to ensure unique workflow ID for every run
            run_id = str(uuid.uuid4())[:8]
            workflow_id = f"{base_id}-{run_id}"
            try:
                await client.start_workflow(
                    workflow_cls.run,
                    {"trace_id": f"cli-trigger-{name}-{run_id}", "env_vars": {}},
                    id=workflow_id,
                    task_queue="database-setup-queue",
                )
                print(f"Started {name.capitalize()} (ID: {workflow_id})")
            except Exception as e:
                print(f"Failed to start {name}: {e}")

    # Trigger all enabled
    await trigger("postgres", PostgresSetupWorkflow, "postgres-setup-workflow")
    await trigger("mongodb", MongodbSetupWorkflow, "mongodb-setup-workflow")
    await trigger("redis", RedisSetupWorkflow, "redis-setup-workflow")
    await trigger("neo4j", Neo4jSetupWorkflow, "neo4j-setup-workflow")
    await trigger("qdrant", QdrantSetupWorkflow, "qdrant-setup-workflow")
    await trigger("minio", MinioSetupWorkflow, "minio-setup-workflow")
    await trigger("clickhouse", ClickhouseSetupWorkflow, "clickhouse-setup-workflow")
    await trigger("opensearch", OpensearchSetupWorkflow, "opensearch-setup-workflow")
    await trigger("cassandra", CassandraSetupWorkflow, "cassandra-setup-workflow")
    await trigger("milvus", MilvusSetupWorkflow, "milvus-setup-workflow")
    await trigger("weaviate", WeaviateSetupWorkflow, "weaviate-setup-workflow")
    await trigger("chroma", ChromaSetupWorkflow, "chroma-setup-workflow")
    
    print(f"Triggered workflows for: {services_to_enable}")

if __name__ == "__main__":
    asyncio.run(main())
