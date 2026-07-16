# LLM Observability Platform Deployment Package (`observability-deploy`)

This config package provides a complete production-ready and development-ready deployment layout for the entire **LLM Observability Platform** stack.

## Architecture & Services Overview

The deployment suite handles **13 integrated services** mapped across datastores, core APIs, scoring engines, and Temporal cron workers.

### 1. Stateful Infrastructure (6 Services)
- **PostgreSQL**: Relational storage for metadata, alerts, and system configuration. Bundles `pgvector` for vector support.
- **Redis**: Low-latency caching, task queues, and DDSketch metrics baseline storage.
- **ClickHouse**: Columnar analytical datastore for long-term telemetry log retention.
- **ZooKeeper**: Service coordinator for Kafka broker health.
- **Kafka**: High-throughput message bus for incoming spans ingestion and async alerts propagation.
- **Temporal**: Workflow engine responsible for orchestrating baseline updates and evaluation.

### 2. Core Application & Scoring Workers (7 Services)
- **`instrumentation-api`**: FastAPI ingestion controller, Grafana UI, and Prometheus exporter dashboard aggregator.
- **`forecast-worker`**: Runs Google TimesFM 2.5-200m forecasting cron every 5 minutes.
- **`toxicity-worker`**: ONNX-based toxicity scorer microservice (`toxic-bert`).
- **`quality-engine`**: Consumes raw spans and coordinates scoring workflows via Temporal.
- **`alert-engine`**: Listens to alert topics in Kafka and dispatches notifications.
- **`temporal-ewma-worker`**: Periodically updates Exponentially Weighted Moving Average cost baselines.
- **`latency-baseline-worker`**: Scrapes Redis DDSketch metrics and upserts hourly latency benchmarks.

---

## Hardware Resource Requirements

Running the full suite of **13 services** concurrently requires a baseline level of system resources due to the integration of stateful databases (ClickHouse, Postgres, Redis), Kafka, Temporal, and model inference workers (Google TimesFM).

### 1. Local Development (Docker Compose)
- **Minimum Requirements**:
  - **RAM**: 12 GB memory allocated to Docker.
  - **CPU**: 4 vCPUs.
  - **Storage**: 30 GB free disk space (SSD recommended).
- **Recommended Configuration**:
  - **RAM**: 16 GB memory.
  - **CPU**: 6 vCPUs.

### 2. Production / Cloud Deployments (EKS/GKE/AKS & Terraform)
- **Kubernetes Nodes**:
  - Minimum of **3 worker nodes** (AWS: `t3.large` or `t3.xlarge`, GCP: `e2-standard-4`, Azure: `Standard_D4s_v5`).
- **Cloud-Managed Databases (Recommended)**:
  - **PostgreSQL**: `db.t3.medium` (AWS), Cloud SQL `db-custom-2-7680` (GCP), or Flexible Server `GP_Standard_D2s_v3` (Azure).
  - **Redis**: `cache.t3.medium` (AWS), MemoryStore (GCP), or Azure Cache for Redis `Standard` tier (Azure).
  - **Kafka**: AWS MSK with 2x `kafka.m5.large` brokers, GCP Managed Kafka, or AKS-native Kafka instances.

---


## Folder Structure

```
packages/configs/observability-deploy/
├── .package-meta.yaml         # Package metadata
├── README.md                  # This file
├── deploy/
│   ├── docker/
│   │   └── docker-compose.yaml # Production-like Docker Compose
│   ├── kubernetes/
│   │   ├── namespace.yaml
│   │   ├── network-policies.yaml # Strict NetworkPolicies
│   │   ├── configmap.yaml
│   │   ├── databases.yaml      # DB Deployments & PVCs
│   │   ├── temporal.yaml       # Temporal setup
│   │   ├── api-deployment.yaml # FastAPI Ingress, Service, Deployment
│   │   ├── workers-deployment.yaml # Microservices and worker workloads
│   │   ├── migrations-job.yaml # Automated database schema migrations
│   │   ├── backup-cronjob.yaml # Automated daily backup scheduler
│   │   └── backup-pvc.yaml     # Backup persistent storage definition
│   └── terraform/
│       ├── aws/                # AWS EKS, RDS, MSK, ElastiCache
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       ├── gcp/                # GCP GKE, Cloud SQL, MemoryStore
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       ├── azure/              # Azure AKS, DB Postgres, Cache Redis
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       └── ansible/            # Ansible playbook and hosts config
│           ├── hosts.ini
│           └── playbook.yaml
└── scripts/
    ├── deploy.sh              # Single Deployment Orchestrator CLI
    ├── backup.sh              # Automated database backup script
    ├── run-migrations.sh      # Unified schema migrations runner
    └── setup-cron.sh          # Local cron backup scheduler setup
```

---

## Getting Started

To begin, make sure you have installed the CLI prerequisites:
- `docker` & `docker-compose`
- `kubectl` (if deploying to Kubernetes)
- `terraform` (if provisioning Cloud infrastructure)
- `ansible` (if deploying to remote VM nodes)

Run the unified orchestrator script from the package root:
```bash
./scripts/deploy.sh
```
Follow the interactive prompts to validate your environment, deploy the local Docker Compose stack, or apply cloud configurations.
