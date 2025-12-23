import os
import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]

if project_root.as_posix() not in sys.path:
    sys.path.insert(0, project_root.as_posix())

import logging
logging.basicConfig(level=logging.INFO)

from temporalio.client import Client
from temporalio.worker import Worker

from infrastructure.orchestrator.activities.network.certificate_manage_activity import generate_certificates_activity, generate_traefik_tls_config_activity
from infrastructure.orchestrator.activities.network.host_manage_activity import add_hosts_entries_activity
from infrastructure.orchestrator.activities.network.virtual_ip_manage_activity import allocate_virtual_ips_activity

from infrastructure.database.shared.create_database_network_activity import create_database_network_activity

from infrastructure.database.postgres.setup.postgres_setup_activity import setup_postgres_activity, teardown_postgres_activity
from infrastructure.database.postgres.setup.postgres_setup_workflow import PostgresSetupWorkflow, PostgresTeardownWorkflow

from infrastructure.database.mongodb.setup.mongodb_setup_activity import setup_mongodb_activity, teardown_mongodb_activity
from infrastructure.database.mongodb.setup.mongodb_setup_workflow import MongodbSetupWorkflow, MongodbTeardownWorkflow

from infrastructure.database.redis.setup.redis_setup_activity import setup_redis_activity, teardown_redis_activity
from infrastructure.database.redis.setup.redis_setup_workflow import RedisSetupWorkflow, RedisTeardownWorkflow

from infrastructure.database.neo4j.setup.neo4j_setup_activity import setup_neo4j_activity, teardown_neo4j_activity
from infrastructure.database.neo4j.setup.neo4j_setup_workflow import Neo4jSetupWorkflow, Neo4jTeardownWorkflow

from infrastructure.database.qdrant.setup.qdrant_setup_activity import setup_qdrant_activity, teardown_qdrant_activity
from infrastructure.database.qdrant.setup.qdrant_setup_workflow import QdrantSetupWorkflow, QdrantTeardownWorkflow

from infrastructure.database.minio.setup.minio_setup_activity import setup_minio_activity, teardown_minio_activity
from infrastructure.database.minio.setup.minio_setup_workflow import MinioSetupWorkflow, MinioTeardownWorkflow

from infrastructure.database.clickhouse.setup.clickhouse_setup_activity import setup_clickhouse_activity, teardown_clickhouse_activity
from infrastructure.database.clickhouse.setup.clickhouse_setup_workflow import ClickhouseSetupWorkflow, ClickhouseTeardownWorkflow

from infrastructure.database.opensearch.setup.opensearch_setup_activity import setup_opensearch_activity, teardown_opensearch_activity
from infrastructure.database.opensearch.setup.opensearch_setup_workflow import OpensearchSetupWorkflow, OpensearchTeardownWorkflow

from infrastructure.database.cassandra.setup.cassandra_setup_activity import setup_cassandra_activity, teardown_cassandra_activity
from infrastructure.database.cassandra.setup.cassandra_setup_workflow import CassandraSetupWorkflow, CassandraTeardownWorkflow

from infrastructure.database.milvus.setup.milvus_setup_activity import setup_milvus_activity, teardown_milvus_activity
from infrastructure.database.milvus.setup.milvus_setup_workflow import MilvusSetupWorkflow, MilvusTeardownWorkflow

from infrastructure.database.weaviate.setup.weaviate_setup_activity import setup_weaviate_activity, teardown_weaviate_activity
from infrastructure.database.weaviate.setup.weaviate_setup_workflow import WeaviateSetupWorkflow, WeaviateTeardownWorkflow

from infrastructure.database.chroma.setup.chroma_setup_activity import setup_chroma_activity, teardown_chroma_activity
from infrastructure.database.chroma.setup.chroma_setup_workflow import ChromaSetupWorkflow, ChromaTeardownWorkflow


async def main():
    print("Starting Database Stack Worker...")
    
    client = await Client.connect("localhost:7233", namespace="default")
    
    worker = Worker(
        client,
        task_queue="database-setup-queue",
        workflows=[
            PostgresSetupWorkflow,
            PostgresTeardownWorkflow,
            MongodbSetupWorkflow,
            MongodbTeardownWorkflow,
            RedisSetupWorkflow,
            RedisTeardownWorkflow,
            Neo4jSetupWorkflow,
            Neo4jTeardownWorkflow,
            QdrantSetupWorkflow,
            QdrantTeardownWorkflow,
            MinioSetupWorkflow,
            MinioTeardownWorkflow,
            ClickhouseSetupWorkflow,
            ClickhouseTeardownWorkflow,
            OpensearchSetupWorkflow,
            OpensearchTeardownWorkflow,
            CassandraSetupWorkflow,
            CassandraTeardownWorkflow,
            MilvusSetupWorkflow,
            MilvusTeardownWorkflow,
            WeaviateSetupWorkflow,
            WeaviateTeardownWorkflow,
            ChromaSetupWorkflow,
            ChromaTeardownWorkflow,
        ],
        activities=[
            create_database_network_activity,
            allocate_virtual_ips_activity,
            generate_certificates_activity,
            generate_traefik_tls_config_activity,
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
            teardown_chroma_activity,
        ]
    )
    
    print("Database Worker started on queue 'database-setup-queue'")
    print("  Workflows: 24 (12 setup + 12 teardown)")
    print("  Activities: 28")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())