# CI/CD Pipeline - Usage Guide

## Quick Start

**1. Start Worker:**
```bash
python infrastructure/cicd/workers/cicd_pipeline_worker.py
```

Or:
```bash
./infrastructure/cicd/workers/start_cicd_worker.sh
```

**2. Run Workflow:**
```python
from temporalio.client import Client
import asyncio

async def deploy():
    client = await Client.connect("localhost:7233")
    
    result = await client.execute_workflow(
        "CICDPipelineWorkflow",
        {
            "application_name": "observability-platform",
            "namespace": "argocd",
            "repo_url": "https://github.com/Chief-Strategist-J/llm-observability-platform",
            "deployment_path": "deployments/observability"
        },
        id="cicd_deployment_1",
        task_queue="cicd-pipeline-queue"
    )
    
    print(f"Deployment result: {result}")

asyncio.run(deploy())
```

## Structure

```
infrastructure/cicd/
├── activities/
│   ├── argocd_deploy_activity.py    # Deploy & sync
│   └── argocd_status_activity.py    # Get status
├── workflows/
│   └── cicd_pipeline_workflow.py    # Main workflow
├── workers/
│   ├── cicd_pipeline_worker.py      # Worker
│   └── start_cicd_worker.sh         # Start script
└── argocd/
    └── applications/
        └── observability.yaml        # ArgoCD app manifest
```

## Activities

**deploy_to_argocd**
- Deploys ArgoCD application
- Uses kubectl apply

**sync_argocd_application**
- Triggers ArgoCD sync
- Uses argocd CLI

**get_argocd_app_status**
- Retrieves application status
- Returns health and sync status

## Workflow Flow

1. Deploy ArgoCD application (kubectl apply)
2. Wait 5s
3. Sync application (argocd app sync)
4. Get status (argocd app get)
5. Complete

## Logging

All logs use LogQL structured format:
```python
logger.info(
    "event_name",
    param=value,
    timestamp=time.time()
)
```

Query in Loki:
```
{service_name="CICDPipelineWorker"} | json | event="deploy"
```

## Testing

```bash
python infrastructure/cicd/workers/cicd_pipeline_worker.py
```

Expected logs:
```
service=CICDPipelineWorker event=worker_start
workflow_start pipeline=cicd
argocd_deploy_completed success=true
argocd_sync_completed success=true
```
