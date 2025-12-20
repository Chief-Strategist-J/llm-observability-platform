import os
import sys
import asyncio
import logging
from pathlib import Path


project_root = Path(__file__).resolve().parents[2]

if project_root.as_posix() not in sys.path:
    sys.path.insert(0, project_root.as_posix())

from temporalio.client import Client
from temporalio.worker import Worker

# Absolute imports with full path
from infrastructure.orchestrator.activities.network.certificate_manage_activity import generate_certificates_activity
from infrastructure.orchestrator.activities.network.host_manage_activity import add_hosts_entries_activity
from infrastructure.orchestrator.activities.network.virtual_ip_manage_activity import allocate_virtual_ips_activity

# Database activities
from infrastructure.database.shared.create_database_network_activity import create_database_network_activity

# Postgres
from infrastructure.database.postgres.setup.postgres_setup_activity import setup_postgres_activity, teardown_postgres_activity
from infrastructure.database.postgres.setup.postgres_setup_workflow import PostgresSetupWorkflow

# MongoDB
from infrastructure.database.mongodb.setup.mongodb_setup_activity import setup_mongodb_activity, teardown_mongodb_activity
from infrastructure.database.mongodb.setup.mongodb_setup_workflow import MongodbSetupWorkflow

# Redis
from infrastructure.database.redis.setup.redis_setup_activity import setup_redis_activity, teardown_redis_activity
from infrastructure.database.redis.setup.redis_setup_workflow import RedisSetupWorkflow

# Neo4j
from infrastructure.database.neo4j.setup.neo4j_setup_activity import setup_neo4j_activity, teardown_neo4j_activity
from infrastructure.database.neo4j.setup.neo4j_setup_workflow import Neo4jSetupWorkflow

# Qdrant
from infrastructure.database.qdrant.setup.qdrant_setup_activity import setup_qdrant_activity, teardown_qdrant_activity
from infrastructure.database.qdrant.setup.qdrant_setup_workflow import QdrantSetupWorkflow

# MinIO
from infrastructure.database.minio.setup.minio_setup_activity import setup_minio_activity, teardown_minio_activity
from infrastructure.database.minio.setup.minio_setup_workflow import MinioSetupWorkflow

# ClickHouse
from infrastructure.database.clickhouse.setup.clickhouse_setup_activity import setup_clickhouse_activity, teardown_clickhouse_activity
from infrastructure.database.clickhouse.setup.clickhouse_setup_workflow import ClickhouseSetupWorkflow

# OpenSearch
from infrastructure.database.opensearch.setup.opensearch_setup_activity import setup_opensearch_activity, teardown_opensearch_activity
from infrastructure.database.opensearch.setup.opensearch_setup_workflow import OpensearchSetupWorkflow

# Cassandra
from infrastructure.database.cassandra.setup.cassandra_setup_activity import setup_cassandra_activity, teardown_cassandra_activity
from infrastructure.database.cassandra.setup.cassandra_setup_workflow import CassandraSetupWorkflow

# Milvus
from infrastructure.database.milvus.setup.milvus_setup_activity import setup_milvus_activity, teardown_milvus_activity
from infrastructure.database.milvus.setup.milvus_setup_workflow import MilvusSetupWorkflow

# Weaviate
from infrastructure.database.weaviate.setup.weaviate_setup_activity import setup_weaviate_activity, teardown_weaviate_activity
from infrastructure.database.weaviate.setup.weaviate_setup_workflow import WeaviateSetupWorkflow

# Chroma
from infrastructure.database.chroma.setup.chroma_setup_activity import setup_chroma_activity, teardown_chroma_activity
from infrastructure.database.chroma.setup.chroma_setup_workflow import ChromaSetupWorkflow

async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("event=worker_startup queue=database-setup-queue")
    
    client = await Client.connect("localhost:7233", namespace="default")
    
    worker = Worker(
        client,
        task_queue="database-setup-queue",
        workflows=[
            PostgresSetupWorkflow,
            MongodbSetupWorkflow,
            RedisSetupWorkflow,
            Neo4jSetupWorkflow,
            QdrantSetupWorkflow,
            MinioSetupWorkflow,
            ClickhouseSetupWorkflow,
            OpensearchSetupWorkflow,
            CassandraSetupWorkflow,
            MilvusSetupWorkflow,
            WeaviateSetupWorkflow,
            ChromaSetupWorkflow
        ],
        activities=[
            create_database_network_activity,
            
            allocate_virtual_ips_activity,
            generate_certificates_activity,
            add_hosts_entries_activity,
            
            setup_postgres_activity,
            teardown_postgres_activity,
            
            setup_mongodb_activity,
            teardown_mongodb_activity,
            
            setup_redis_activity,
            teardown_redis_activity,

            setup_neo4j_activity,
            teardown_neo4j_activity,

            setup_qdrant_activity,
            teardown_qdrant_activity,

            setup_minio_activity,
            teardown_minio_activity,

            setup_clickhouse_activity,
            teardown_clickhouse_activity,

            setup_opensearch_activity,
            teardown_opensearch_activity,

            setup_cassandra_activity,
            teardown_cassandra_activity,

            setup_milvus_activity,
            teardown_milvus_activity,

            setup_weaviate_activity,
            teardown_weaviate_activity,

            setup_chroma_activity,
            teardown_chroma_activity
        ]
    )
    
    logger.info("event=worker_started queue=database-setup-queue workflows=12 activities=27")
    print("Unified Database Stack Worker started on queue 'database-setup-queue'")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())