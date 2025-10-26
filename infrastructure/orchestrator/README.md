# **Temporal Orchestrator — README**

## 1. Overview

This directory contains a **Temporal.io orchestration system** for managing containerized services in the LLM chatbot infrastructure.

**Components:**

* **Activities** – Individual operations (e.g., container start/stop, monitoring).
* **Workflows** – Orchestration logic to coordinate activities.
* **Workers** – Poll task queues and execute workflows/activities.
* **Temporal Server** – Manages state and workflow durability.
* **Trigger / Stop scripts** – Start or terminate workflows, organized per service.

---

## 2. Folder Structure

```
temporal-orchestrator/
│
├── activities/
│   ├── ai_proxy_container_activity.py
│   ├── my_new_activity.py           # Example new activity
│   └── common_activity/
│       ├── start_grafana_activity.py
│       ├── configure_grafana_activity.py
│       ├── loki_activity.py
│       ├── otel_activity.py
│       ├── promotheus_activity.py
│       └── promtail_activity.py
│
├── dynamicconfig/
│   └── development-sql.yaml
│
├── workflows/
│   ├── logging_pipeline_workflow.py
│   └── my_new_workflow.py           # Example new workflow
│
├── workers/
│   ├── logging_pipeline_worker.py
│   └── my_new_worker.py             # Example new worker
│
├── trigger/
│   └── ai_proxy_container/          # Example service folder
│       ├── start.py
│       └── stop.py
│   └── knowledge_graph/             # Example service folder
│       ├── start.py
│       └── stop.py
│
├── temporal-orchestrator-compose.yaml
└── README.md
```

> **Note:** Each new service gets its own folder under `trigger/` with its `start.py` and `stop.py` scripts.

---

## 3. Adding a New Activity

**Path:** `activities/my_new_activity.py`

```python
from temporalio import activity
import asyncio

@activity.defn
async def my_new_activity(arg: str) -> str:
    """Minimal new activity"""
    await asyncio.sleep(0.1)
    return f"done:{arg}"
```

---

## 4. Adding a New Workflow

**Path:** `workflows/my_new_workflow.py`

```python
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

@workflow.defn
class MyNewWorkflow:
    @workflow.run
    async def run(self, param: str) -> str:
        from activities.my_new_activity import my_new_activity

        result = await workflow.execute_activity(
            my_new_activity,
            param,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=10),
            ),
        )
        return result
```

---

## 5. Adding a New Worker (Independent)

**Path:** `workers/my_new_worker.py`

```python
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflows.my_new_workflow import MyNewWorkflow
from activities.my_new_activity import my_new_activity

async def main():
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="my-new-task-queue",
        workflows=[MyNewWorkflow],
        activities=[my_new_activity]
    )
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
```

> No edits to existing workers are required.

---

## 6. Trigger Script for a Service

**Path:** `trigger/knowledge_graph/start.py`

```python
import asyncio
from temporalio.client import Client
from workflows.my_new_workflow import MyNewWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    result = await client.execute_workflow(
        MyNewWorkflow.run,
        "input-value",
        id="knowledge_graph_1",
        task_queue="my-new-task-queue",
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 7. Stop Script for a Service

**Path:** `trigger/knowledge_graph/stop.py`

```python
import asyncio
from temporalio.client import Client

async def main():
    client = await Client.connect("localhost:7233")
    await client.terminate_workflow("knowledge_graph_1", reason="manual stop")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 8. Commands

### Start Temporal Infrastructure

```bash
cd infrastructure/orchestrator
docker-compose -f temporal-orchestrator-compose.yaml down -v
docker system prune -f
docker-compose -f temporal-orchestrator-compose.yaml up -d
```

### Verify Services

```bash
docker ps
curl http://localhost:8080/api/v1/namespaces/default
docker exec temporal-postgresql psql -U temporal -d temporal -c "SELECT 1;"
```

### Start New Worker

```bash
cd workers
python3 my_new_worker.py
```

### Trigger Service Workflow

```bash
cd trigger/knowledge_graph
python3 start.py
```

### Stop Service Workflow

```bash
cd trigger/knowledge_graph
python3 stop.py
```

### Stop Infrastructure

```bash
docker-compose -f temporal-orchestrator-compose.yaml down
```

---

## 9. Visual Pipeline (for Knowledge Graph Service)

```
[Trigger Script]         trigger/knowledge_graph/start.py
       │
       ▼
[Temporal Server]         localhost:7233
       │
       ▼
[Worker]                  workers/my_new_worker.py
       │
       ▼
[Workflow Execution]      workflows/my_new_workflow.py
       │
       └─► calls activities/my_new_activity.py
       │
       ▼
[Results / State]         Temporal DB (Postgres)
       │
       ▼
[Web UI / Logs]           http://localhost:8080
```

---
