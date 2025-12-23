import asyncio
import sys
from pathlib import Path
from temporalio.client import Client

project_root = Path(__file__).resolve().parents[2]
if project_root.as_posix() not in sys.path:
    sys.path.insert(0, project_root.as_posix())


async def list_active_workflows(client: Client, namespace: str = "default") -> list:
    workflows = []
    async for wf in client.list_workflows(query="ExecutionStatus='Running'"):
        workflows.append({
            "id": wf.id,
            "type": wf.workflow_type,
            "status": wf.status,
        })
    return workflows


async def terminate_workflow(client: Client, workflow_id: str) -> dict:
    try:
        handle = client.get_workflow_handle(workflow_id)
        await handle.terminate("User requested termination")
        return {"id": workflow_id, "terminated": True}
    except Exception as e:
        return {"id": workflow_id, "terminated": False, "error": str(e)}


async def main():
    client = await Client.connect("localhost:7233", namespace="default")
    
    database_workflow_prefixes = [
        "postgres-setup",
        "mongodb-setup",
        "redis-setup",
        "neo4j-setup",
        "qdrant-setup",
        "minio-setup",
        "clickhouse-setup",
        "opensearch-setup",
        "cassandra-setup",
        "milvus-setup",
        "weaviate-setup",
        "chroma-setup",
    ]
    
    print("Listing active workflows...")
    active_workflows = await list_active_workflows(client)
    
    if not active_workflows:
        print("No active workflows found.")
        return
    
    print(f"Found {len(active_workflows)} active workflows:")
    for wf in active_workflows:
        print(f"  - {wf['id']} ({wf['type']})")
    
    terminated = []
    for wf in active_workflows:
        for prefix in database_workflow_prefixes:
            if wf["id"].startswith(prefix):
                print(f"Terminating {wf['id']}...")
                result = await terminate_workflow(client, wf["id"])
                terminated.append(result)
                break
    
    print(f"\nTerminated {len(terminated)} database workflows:")
    for t in terminated:
        status = "OK" if t["terminated"] else f"FAILED: {t.get('error', 'unknown')}"
        print(f"  - {t['id']}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
