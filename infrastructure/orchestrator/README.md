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
cd ../..

source /home/j/live/dinesh/llm-chatbot-python/.venv/bin/activate

```

### Verify Services

```bash
docker ps
curl http://0.0.0.0:8080/namespaces/default/workflows
docker exec temporal-postgresql psql -U temporal -d temporal -c "SELECT 1;"
```

### Start Your Worker

```bash
cd workers
python3 my_new_worker.py

// start workers

source /home/j/live/dinesh/llm-chatbot-python/.venv/bin/activate


python infrastructure/orchestrator/workers/logs_pipeline_worker.py 

python infrastructure/orchestrator/workers/database_pipeline_worker.py 

python infrastructure/orchestrator/workers/metrics_pipeline_worker.py 

python infrastructure/orchestrator/workers/tracing_pipeline_worker.py 

python service/llm_chat_app/worker/workers/chat_worker.py 

python infrastructure/observability/workers/logs_pipeline_worker.py



```

### Trigger Service Workflow

```bash
cd trigger/knowledge_graph
python3 start.py

// Trigger Service Workflow

python infrastructure/orchestrator/trigger/common/logs_pipeline_start.py 

python infrastructure/orchestrator/trigger/common/database_pipeline_start.py 

python infrastructure/orchestrator/trigger/common/metrics_pipeline_start.py 

python infrastructure/orchestrator/trigger/common/tracing_pipeline_start.py 

python infrastructure/orchestrator/trigger/common/run_logs_pipeline_then_stdout_ingest.py

python infrastructure/orchestrator/trigger/common/start_application_stdout_ingest.py

python service/llm_chat_app/worker/workflows/chat_setup_workflow.py

python service/llm_chat_app/worker/workflows/chat_cleanup_workflow.py 




```

### Logs Pipeline Workflow

```bash
START
 │
 │── Receive `params`
 │
 │── Configure Retry Policy
 │      • initial_interval = 1s
 │      • maximum_interval = 10s
 │      • maximum_attempts = 3
 │
 │── Set Activity Timeout
 │      • start_to_close_timeout = 5 minutes
 │
 │
 ├── Step 1: Stop OpenTelemetry Collector
 │        Activity: stop_opentelemetry_collector(params)
 │        Behavior:
 │           - Retries based on RetryPolicy
 │           - Fails workflow if all retry attempts fail
 │
 ├── Step 2: Delete OpenTelemetry Collector
 │        Activity: delete_opentelemetry_collector(params)
 │        Behavior:
 │           - Same retry/timeout controls
 │
 ├── Step 3: Start OpenTelemetry Collector
 │        Activity: start_opentelemetry_collector(params)
 │        Behavior:
 │           - Ensures collector is active again for pipeline
 │
 ├── Step 4: Start Loki Service
 │        Activity: start_loki_activity(params)
 │        Behavior:
 │           - Initiates Loki to ingest logs
 │
 ├── Step 5: Start Grafana Service
 │        Activity: start_grafana_activity(params)
 │        Behavior:
 │           - Ensures Grafana is up to visualize the logs
 │
 │
 └── END → Return message:
         "Logs pipeline fully configured"

```


### Database Pipeline Workflow

```bash
START
  │
  ▼
Receive `service_name`
  │
  ▼
──────────────────────────────────────────────
Step 1: Start Neo4j Container
  │     Activity: start_neo4j_container(service_name)
  │     Behavior:
  │       - start_to_close_timeout = 5 minutes
  │       - retry_policy: maximum_attempts = 3
  ▼
──────────────────────────────────────────────
Step 2: Start Qdrant Container
  │     Activity: start_qdrant_container(service_name)
  │     Behavior:
  │       - start_to_close_timeout = 5 minutes
  │       - retry_policy: maximum_attempts = 3
  ▼
──────────────────────────────────────────────
END → "Database pipeline fully configured: Neo4j + Qdrant"

```

### Metrics Pipeline Workflow

```bash
START
  │
  ▼
Receive `params`
  │
  ▼
Validate params
  │      • Must be dict
  │      • Must contain service_name (string)
  │
  ├── If invalid → END → "Error: Invalid params provided"
  ├── If missing/invalid service_name → END → "Error: service_name is required and must be string"
  │
  ▼
Configure Retry Policy
  │      • initial_interval = 1s
  │      • maximum_interval = 10s
  │      • maximum_attempts = 3
  │
  ▼
Set Activity Timeout
  │      • start_to_close_timeout = 5 minutes
  │
  ▼
──────────────────────────────────────────────
Step 1: Start Prometheus Container
  │     Activity: start_prometheus_container(params)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses timeout
  │       - Returns truthy if successful
  │
  ├── If result is falsy → END → "Error: Failed to start Prometheus container"
  │
  ▼
Sleep 2 seconds
  │
  ▼
──────────────────────────────────────────────
Step 2: Start Grafana Container
  │     Activity: start_grafana_container(params)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses timeout
  │       - Returns truthy if successful
  │
  ├── If result is falsy → END → "Error: Failed to start Grafana container"
  │
  ▼
──────────────────────────────────────────────
END → "Metrics pipeline fully configured: Prometheus + Grafana + Dashboard"
──────────────────────────────────────────────
EXCEPTION HANDLING
  │
  └── If any exception occurs:
          END → "Error: Metrics pipeline failed: <error>"


```


### Tracing Pipeline Workflow

```bash
START
  │
  ▼
Receive `params`
  │
  ▼
Validate params
  │      • Must be dict
  │      • Must contain service_name (string)
  │
  ├── If invalid → END → "Error: Invalid params provided"
  ├── If missing/invalid service_name → END → "Error: service_name is required and must be string"
  │
  ▼
Configure Retry Policy
  │      • initial_interval = 1s
  │      • maximum_interval = 10s
  │      • maximum_attempts = 3
  │
  ▼
Set Activity Timeout
  │      • start_to_close_timeout = 5 minutes
  │
  ▼
──────────────────────────────────────────────
Step 1: Start Jaeger Container
  │     Activity: start_jaeger_container(params)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses timeout
  │       - Returns truthy if successful
  │
  ├── If result is falsy → END → "Error: Failed to start Jaeger container"
  │
  ▼
Sleep 2 seconds
  │
  ▼
──────────────────────────────────────────────
Step 2: Start Grafana Container
  │     Activity: start_grafana_container(params)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses timeout
  │       - Returns truthy if successful
  │
  ├── If result is falsy → END → "Error: Failed to start Grafana container"
  │
  ▼
──────────────────────────────────────────────
END → "Tracing pipeline fully configured: Jaeger + Grafana + Dashboard"
──────────────────────────────────────────────
EXCEPTION HANDLING
  │
  └── If any exception occurs:
          END → "Error: Tracing pipeline failed: <error>"


```


### Application Stdout Ingest Workflow

```bash
START
  │
  ▼
Receive `params`
  │
  ▼
Configure Retry Policy
  │      • maximum_attempts = 3
  │
  ▼
Set Timeouts
  │      • t = 5 minutes
  │      • some steps = 30 seconds
  │
  ▼
──────────────────────────────────────────────
Step 1: Configure Application Stdout Pipeline
  │     Activity: logs_configure_activity(params)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 5-minute timeout
  │       - Returns configuration object
  │
  ├── If conf is falsy → END → "configuration failed"
  │
  ▼
──────────────────────────────────────────────
Step 2: Add Loki Datasource
  │     Activity: add_loki_datasource_activity(params)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 30-second timeout
  ▼
──────────────────────────────────────────────
Sleep 5 seconds
  │
  ▼
──────────────────────────────────────────────
Step 3: Discover Local Log Files
  │     Activity: discover_log_files_activity(conf)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 5-minute timeout
  ▼
──────────────────────────────────────────────
Step 4: Discover Docker Log Files
  │     Activity: discover_docker_logs_activity(conf)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 5-minute timeout
  ▼
──────────────────────────────────────────────
Merge Discoveries
  │      • local_logs + docker_logs
  │      • Remove duplicates
  │      • Sort list
  ▼
──────────────────────────────────────────────
Step 5: Enrich Logs With Labels
  │     Activity: label_enrichment_activity(
  │         {"files": discovered, "labels": conf.get("labels", {})}
  │     )
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 5-minute timeout
  ▼
──────────────────────────────────────────────
Build Shipping Parameters
  │      • files = enriched[].path
  │      • labels = enriched[0].labels OR conf.labels
  │      • protocol = otlp
  │      • endpoint = http://localhost:4318
  │      • batch_size
  │      • flush_interval_seconds
  │      • timeout_seconds = 10
  ▼
──────────────────────────────────────────────
Step 6: Tail and Ship Logs
  │     Activity: tail_and_ship_logs_activity(ship_params)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 30-second timeout
  ▼
──────────────────────────────────────────────
END → "ingest started: discovered={len(discovered)} enriched={len(enriched)} status={result.status}"

```



### Container Logs Ingest Workflow

```bash
START
  │
  ▼
Receive inputs
  │      • template_path: str
  │      • log_paths: list
  │      • service_name: str
  │      • loki_endpoint: str
  │
  ▼
Configure Retry Policy
  │      • initial_interval = 1s
  │      • maximum_interval = 10s
  │      • maximum_attempts = 3
  │
  ▼
Set Timeout
  │      • start_to_close_timeout = 5 minutes
  │
  ▼
──────────────────────────────────────────────
Step 1: Generate and Validate Config
  │     Activity: generate_and_validate_config_activity(
  │         template_path,
  │         log_paths,
  │         service_name,
  │         loki_endpoint
  │     )
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses timeout
  │       - Returns config_str
  ▼
──────────────────────────────────────────────
Step 2: Push and Reload Configuration
  │     Activity: push_and_reload_activity(config_str)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses timeout
  ▼
──────────────────────────────────────────────
END → "container_logs ingest configured"


```

### OTLP from Apps Ingest Workflow

```bash
START
  │
  ▼
Receive inputs
  │      • template_path: str
  │      • service_name: str
  │      • otlp_endpoint: str
  │
  ▼
Configure Retry Policy
  │      • initial_interval = 1s
  │      • maximum_interval = 10s
  │      • maximum_attempts = 3
  │
  ▼
Set Timeout
  │      • start_to_close_timeout = 5 minutes
  │
  ▼
──────────────────────────────────────────────
Step 1: Enable OTLP Receiver
  │     Activity: enable_otlp_receiver_activity(
  │         template_path,
  │         service_name,
  │         otlp_endpoint
  │     )
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses timeout
  │       - Produces config_path
  ▼
──────────────────────────────────────────────
Step 2: Collect and Route OTLP Traffic
  │     Activity: collect_and_route_otlp_activity(config_path)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses timeout
  ▼
──────────────────────────────────────────────
END → "otlp_from_apps ingest enabled"
```


### Chat Setup Workflow

```bash
START
  │
  ▼
Receive `params`
  │
  ▼
Clone params → p
  │      • p["context"] = "/home/j/live/dinesh/llm-chatbot-python/service/llm_chat_app"
  │
  ▼
Log: "ChatSetupWorkflow start"
  │
  ▼
Configure Retry Policy
  │      • initial_interval = 2s
  │      • maximum_interval = 10s
  │      • maximum_attempts = 3
  │
  ▼
Set Timeout
  │      • start_to_close_timeout = 10 minutes
  │
  ▼
──────────────────────────────────────────────
Step 1: Start Neo4j Dependency
  │     Activity: start_neo4j_dependency_activity(p)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 10-minute timeout
  ▼
──────────────────────────────────────────────
Step 2: Verify Cloudflare Dependency
  │     Activity: verify_cloudflare_dependency_activity(p)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 10-minute timeout
  ▼
──────────────────────────────────────────────
Step 3: Build Chat Image
  │     Activity: build_chat_image_activity(p)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 10-minute timeout
  ▼
──────────────────────────────────────────────
Step 4: Run Chat Container
  │     Activity: run_chat_container_activity(p)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 10-minute timeout
  ▼
──────────────────────────────────────────────
Step 5: Check Chat Health
  │     Activity: check_chat_health_activity(p)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 10-minute timeout
  ▼
──────────────────────────────────────────────
Log: "ChatSetupWorkflow complete"
  │
  ▼
END → "chat_setup_complete"

```


### Chat Cleanup Workflow

```bash
START
  │
  ▼
Receive `params`
  │
  ▼
Log: "ChatCleanupWorkflow start"
  │
  ▼
Configure Retry Policy
  │      • initial_interval = 2s
  │      • maximum_interval = 10s
  │      • maximum_attempts = 3
  │
  ▼
Set Timeout
  │      • start_to_close_timeout = 10 minutes
  │
  ▼
──────────────────────────────────────────────
Step 1: Stop Chat Container
  │     Activity: stop_chat_container_activity(params)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 10-minute timeout
  ▼
──────────────────────────────────────────────
Step 2: Delete Chat Container
  │     Activity: delete_chat_container_activity(params)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 10-minute timeout
  ▼
──────────────────────────────────────────────
Step 3: Delete Chat Image
  │     Activity: delete_chat_image_activity(params)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 10-minute timeout
  ▼
──────────────────────────────────────────────
Step 4: Stop Neo4j Dependency
  │     Activity: stop_neo4j_dependency_activity(params)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 10-minute timeout
  ▼
──────────────────────────────────────────────
Step 5: Delete Neo4j Dependency
  │     Activity: delete_neo4j_dependency_activity(params)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 10-minute timeout
  ▼
──────────────────────────────────────────────
Log: "ChatCleanupWorkflow complete"
  │
  ▼
END → "chat_cleanup_complete"


```


### Flyio Deployment Workflow

```bash
START
  │
  ▼
Receive `params`
  │
  ▼
Clone params → p
  │      • p.setdefault("service_name", "flyio-deploy")
  │
  ▼
Log: "FlyioDeploymentWorkflow start"
  │
  ▼
Configure Retry Policy
  │      • initial_interval = 2s
  │      • maximum_interval = 10s
  │      • maximum_attempts = 3
  │
  ▼
Set Timeout
  │      • start_to_close_timeout = 15 minutes
  │
  ▼
──────────────────────────────────────────────
Step 1: Generate Deployment Configs
  │     Activity: generate_deployment_configs_activity(
  │         {**p, "platforms": ["flyio"]}
  │     )
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  ▼
──────────────────────────────────────────────
Step 2: Create Fly.io App
  │     Activity: create_flyio_app_activity(p)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  ▼
──────────────────────────────────────────────
Step 3: Set Fly.io Secrets
  │     Activity: set_flyio_secrets_activity(p)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  ▼
──────────────────────────────────────────────
Step 4: Deploy to Fly.io
  │     Activity: deploy_to_flyio_activity(p)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  │       - Produces deploy_result dict (possibly)
  ▼
──────────────────────────────────────────────
Determine Deployment URL
  │      • If deploy_result contains "deployment_url" → use it
  │      • Else fallback: https://{app_name}.fly.dev
  ▼
──────────────────────────────────────────────
Step 5: Check Deployment Health
  │     Condition: deployment_url is truthy
  │     Activity: check_deployment_health_activity(
  │         {**p, "url": deployment_url}
  │     )
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  ▼
──────────────────────────────────────────────
Log: "FlyioDeploymentWorkflow complete"
  │
  ▼
END → "flyio_deploy_complete"


```


### Railway Deployment Workflow

```bash
START
  │
  ▼
Receive `params`
  │
  ▼
Clone params → p
  │      • p.setdefault("service_name", "railway-deploy")
  │
  ▼
Log: "RailwayDeploymentWorkflow start"
  │
  ▼
Configure Retry Policy
  │      • initial_interval = 2s
  │      • maximum_interval = 10s
  │      • maximum_attempts = 3
  │
  ▼
Set Timeout
  │      • start_to_close_timeout = 15 minutes
  │
  ▼
──────────────────────────────────────────────
Step 1: Generate Deployment Configs
  │     Activity: generate_deployment_configs_activity(
  │         {**p, "platforms": ["railway"]}
  │     )
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  ▼
──────────────────────────────────────────────
Step 2: Create Railway Project
  │     Activity: create_railway_project_activity(p)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  ▼
──────────────────────────────────────────────
Step 3: Set Railway Environment Variables
  │     Activity: set_railway_env_vars_activity(p)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  ▼
──────────────────────────────────────────────
Step 4: Deploy to Railway
  │     Activity: deploy_to_railway_activity(p)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  │       - Produces deploy_result dict (maybe)
  ▼
──────────────────────────────────────────────
Determine Deployment URL
  │      • If deploy_result is dict → deployment_url = deploy_result["deployment_url"]
  │      • Else → deployment_url = None
  ▼
──────────────────────────────────────────────
Step 5: Check Deployment Health
  │     Condition: deployment_url is truthy
  │     Activity: check_deployment_health_activity(
  │         {**p, "url": deployment_url}
  │     )
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  ▼
──────────────────────────────────────────────
Log: "RailwayDeploymentWorkflow complete"
  │
  ▼
END → "railway_deploy_complete"


```


### Render Deployment Workflow

```bash
START
  │
  ▼
Receive `params`
  │
  ▼
Clone params → p
  │      • p.setdefault("service_name", "render-deploy")
  │
  ▼
Log: "RenderDeploymentWorkflow start"
  │
  ▼
Configure Retry Policy
  │      • initial_interval = 2s
  │      • maximum_interval = 10s
  │      • maximum_attempts = 3
  │
  ▼
Set Timeout
  │      • start_to_close_timeout = 15 minutes
  │
  ▼
──────────────────────────────────────────────
Step 1: Generate Deployment Configs
  │     Activity: generate_deployment_configs_activity(
  │         {**p, "platforms": ["render"]}
  │     )
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  ▼
──────────────────────────────────────────────
Step 2: Create Render Blueprint
  │     Activity: create_render_blueprint_activity(p)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  ▼
──────────────────────────────────────────────
Step 3: Push Code to GitHub
  │     Activity: push_to_github_activity(p)
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  │       - Produces push_result dict (maybe)
  ▼
──────────────────────────────────────────────
Step 4: Deploy to Render
  │     Activity: deploy_to_render_activity(
  │         {**p, **(push_result or {})}
  │     )
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  ▼
──────────────────────────────────────────────
Determine Deployment URL
  │      • If push_result contains deployment_url → use it
  │      • Else fallback to push_result.repo_url
  │
  ▼
──────────────────────────────────────────────
Step 5: Check Deployment Health
  │     Condition: deployment_url is truthy
  │     Activity: check_deployment_health_activity(
  │         {**p, "url": deployment_url}
  │     )
  │     Behavior:
  │       - Uses retry_policy
  │       - Uses 15-minute timeout
  ▼
──────────────────────────────────────────────
Log: "workflow RenderDeploymentWorkflow complete"
  │
  ▼
END → "render_deploy_complete"



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

# 🌲 **MASTER EXECUTION + RELATIONSHIP TREE**

```
PIPELINE_SYSTEM
│
├─ CONTROL_PLANE  (META: decisions, identity, routing, meaning)
│   │
│   ├─ WorkflowConfig  (meta config)
│   │     │
│   │     ├─ service_name        = logical pipeline identity
│   │     ├─ workflow_name       = workflow class to start
│   │     ├─ task_queue          = execution route (auto: <service_name>-queue)
│   │     ├─ temporal_host       = cluster connection target
│   │     └─ web_ui_url          = observation URL (optional / meta only)
│   │
│   ├─ PipelineExecutor  (meta orchestrator)
│   │     │
│   │     ├─ reads WorkflowConfig
│   │     ├─ connects to temporal_host
│   │     └─ start_workflow(
│   │           workflow_name,
│   │           arg = service_name,
│   │           task_queue = task_queue
│   │        )
│   │
│   └─ Workflow State Machine (meta logic)
│         │
│         └─ Describes *order* of operations (not actual work):
│                start_opentelemetry → start_loki → start_grafana → return result
│
└────────────────────→ TRAVEL ACROSS NETWORK
                            (Temporal API call)
```

---

# 🛰️ **TEMPORAL ROUTING LAYER (Control → Execution Bridge)**

```
TEMPORAL_SERVER
│
├─ Receives workflow start request
│
├─ Creates Workflow Execution History (META: deterministic timeline)
│
└─ SCHEDULE_WORKFLOW_TASK
       │
       └─ Route by queue:
           task_queue = "<service_name>-queue"
```

**This is the critical relationship:**

```
WorkflowConfig.task_queue  MUST MATCH  WorkerConfig.task_queue
```

This is the **binding point** of the system.

---

# ⚙️ **DATA_PLANE (Execution Happens Here)**

```
DATA_PLANE
│
├─ WorkerConfig  (meta execution environment description)
│   │
│   ├─ host           = temporal endpoint
│   ├─ task_queue     = execution queue (same as WorkflowConfig)
│   ├─ namespace      = logical tenant
│   └─ max_concurrency  (optional runtime tuning)
│
├─ Worker (runtime executor process)
│   │
│   ├─ Registers:
│   │     - Workflows: [LogsPipelineWorkflow]
│   │     - Activities: [start_loki, start_grafana, etc]
│   │
│   └─ Listens on task_queue
│         │
│         └─ When workflow tasks arrive → run workflow logic step-by-step
│
└─ Activity Executor (real work happens here)
      │
      ├─ start_opentelemetry_collector(service_name)
      ├─ start_loki_activity(service_name)
      ├─ start_grafana_activity(service_name)
      └─ etc...
      │
      └─ These functions produce **real side-effects**:
            - Launch containers
            - Configure services
            - Apply setup changes
```

---

# 🎛️ **WORKFLOW EXECUTION PLAY-BY-PLAY**

```
Workflow (META: high-level sequence)
│
└─ Step 1: schedule activity: start_opentelemetry_collector
      │
      └─ Temporal routes → Worker → Activity executes (real work)
             │
             └─ Return OK → Workflow proceeds

└─ Step 2: schedule activity: start_loki_activity
      │
      (same dispatch-execute-return pattern)

└─ Step 3: schedule activity: start_grafana_activity

└─ Workflow returns: "Logs pipeline fully configured"
```

---

# ⚡ RELATIONSHIP CLASSIFICATION (Final clarity)

| Relationship                                        | Direction    | Type              | Explanation                                   |
| --------------------------------------------------- | ------------ | ----------------- | --------------------------------------------- |
| PipelineExecutor → WorkflowConfig                   | uses         | META              | Executor reads config to know *what to start* |
| PipelineExecutor → Temporal Server                  | commands     | CONTROL           | Executor tells Temporal to create workflow    |
| WorkflowConfig.task_queue ↔ WorkerConfig.task_queue | binding link | ROUTING           | Ensures workflow tasks and worker match       |
| Temporal Server → Worker                            | dispatches   | EXECUTION ROUTING | Server delivers tasks to worker queue         |
| Worker → Workflow                                   | hosts        | EXECUTION CONTEXT | Worker runs workflow state machine            |
| Workflow → Activities                               | delegates    | TASK EXECUTION    | Workflow requests work, activities do work    |
| Activities → External Systems                       | acts         | REAL EFFECT       | System state changes happen here              |

---
