# Deployment Guide

## Quick Start

### Docker (Now)

**Start Observability Stack:**
```bash
cd deployments/docker
docker-compose -f docker-compose.observability.yml up -d
```

**Stop Stack:**
```bash
docker-compose -f docker-compose.observability.yml down
```

**View Logs:**
```bash
docker-compose -f docker-compose.observability.yml logs -f loki
```

### Kubernetes (Future)

**Deploy to Cluster:**
```bash
kubectl apply -f deployments/kubernetes/base/namespace.yaml
kubectl apply -f deployments/kubernetes/base/
```

**Check Status:**
```bash
kubectl get pods -n observability
kubectl get svc -n observability
```

**Delete:**
```bash
kubectl delete -f deployments/kubernetes/base/
```

## Using Deployment Adapter

**Set Target:**
```bash
export DEPLOY_TARGET=docker       # For Docker
export DEPLOY_TARGET=kubernetes   # For Kubernetes
```

**In Code:**
```python
from infrastructure.orchestrator.deployment.deployment_adapter import DeploymentAdapter

adapter = DeploymentAdapter()

adapter.deploy("loki", {
    "image": "grafana/loki:latest",
    "name": "loki-instance-0"
})

adapter.status("loki")
```

**Adapter auto-detects backend from DEPLOY_TARGET!**

## Migration Path

**Phase 1 (Now):** Docker
```bash
export DEPLOY_TARGET=docker
python infrastructure/observability/workers/logs_pipeline_worker.py
```

**Phase 2 (Future):** Kubernetes
```bash
export DEPLOY_TARGET=kubernetes
python infrastructure/observability/workers/logs_pipeline_worker.py
```

**Same workflow, different backend!**

## Structure

```
deployments/
├── docker/
│   └── docker-compose.observability.yml  # Docker Compose
└── kubernetes/
    └── base/
        ├── namespace.yaml
        ├── loki.yaml
        ├── grafana.yaml
        └── prometheus.yaml
```

## Access URLs

**Docker:**
- Grafana: http://localhost:31001
- Loki: http://localhost:31002
- Prometheus: http://localhost:9090

**Kubernetes:**
```bash
kubectl port-forward svc/grafana 3000:3000 -n observability
kubectl port-forward svc/loki 3100:3100 -n observability
```
