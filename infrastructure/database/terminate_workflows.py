import asyncio
import logging
from temporalio.client import Client

async def main():
    client = await Client.connect("localhost:7233")
    
    ids = [
        "postgres-setup-workflow-id", 
        "mongodb-setup-workflow-id", 
        "redis-setup-workflow-id",
        "neo4j-setup-workflow-id",
        "qdrant-setup-workflow-id",
        "minio-setup-workflow-id",
        "clickhouse-setup-workflow-id",
        "opensearch-setup-workflow-id",
        "cassandra-setup-workflow-id",
        "milvus-setup-workflow-id",
        "weaviate-setup-workflow-id",
        "chroma-setup-workflow-id"
    ]

    for wf_id in ids:
        try:
            handle = client.get_workflow_handle(wf_id)
            await handle.terminate("User requested sequential testing stop")
            print(f"Terminated {wf_id}")
        except Exception as e:
            # Workflow might not exist or already be done
            print(f"Skipped {wf_id}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
