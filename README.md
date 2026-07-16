# LLM Observability Platform

A premium, enterprise-grade, and self-hosted observability suite for Large Language Model (LLM) applications. Capture real-time spans, trace call latencies, calculate token costs, generate semantic embeddings, scan for PII/injections, and proactively forecast usage trends.

---

## Key Features

- **Zero-Code Auto-Instrumentation**: Automatically patches OpenAI, Anthropic, LiteLLM, and LangChain clients.
- **Proactive Cost Forecasting**: Integrates Google's **TimesFM 2.5-200m** time-series model to project cost trends 24 hours ahead.
- **Toxicity & Quality Scoring**: Automatically scores prompts and responses via ONNX classifiers (`toxic-bert`) and registers human review SLOs.
- **Inline Security Scanning**: Built-in Aho-Corasick trie engine to redact structural PII and flag prompt injections.
- **Asynchronous Prompt Embeddings**: Asynchronously maps ingested prompts to 384-dimensional semantic vectors via MiniLM.
- **Resilient Telemetry**: Implements an in-memory queue, SQLite WAL local fallback, and auto-replay sequence for offline fault resilience.

---

## System Architecture

```
                               ┌───────────────────────────┐
                               │     Client App (Python)    │
                               └─────────────┬─────────────┘
                                             │ (Auto-instrumentation)
                                             ▼
                               ┌───────────────────────────┐
                               │  instrumentation-sdk-api  │
                               └──────┬──────┬──────┬──────┘
                                      │      │      │
           ┌──────────────────────────┘      │      └──────────────────────────┐
           ▼ (Write Spans)                   ▼ (Scrape Metrics)                ▼ (OTLP Traces)
┌──────────────────────┐           ┌────────────────────┐            ┌────────────────────┐
│      Kafka Bus       │           │     Prometheus     │            │    Grafana Tempo   │
└──────────┬───────────┘           └─────────┬──────────┘            └─────────┬──────────┘
           │ (Consume)                       │                                 │
           ▼                                 ▼                                 │
┌──────────────────────┐           ┌────────────────────┐                      │
│    Quality Engine    │           │    Grafana UI      │◄─────────────────────┘
└──────────┬───────────┘           └────────────────────┘
           │ (Score POST)
           ▼
┌──────────────────────┐
│   Toxicity Worker    │
└──────────────────────┘
```

### The 13 Integrated Services
1. **`zookeeper`**: Coordinates Kafka brokers.
2. **`kafka`**: Ingests spans and distributes alert topics.
3. **`postgres`**: Relational store with `pgvector` for vector lookups.
4. **`clickhouse`**: Columnar datastore for high-volume telemetry logs.
5. **`redis`**: Low-latency cache for baseline metrics sketches.
6. **`temporal`**: Orchestrates scoring, baseline EWMA, and baseline latency workflows.
7. **`instrumentation-api`**: FastAPI HTTP gateway, Grafana console, and Prometheus exporter.
8. **`forecast-worker`**: Cron executor running TimesFM inference.
9. **`toxicity-worker`**: Microservice hosting the ONNX toxicity classifier.
10. **`quality-engine`**: Kafka consumer executing evaluators via Temporal workflows.
11. **`alert-engine`**: Consumes Kafka alerts and sends Slack/PagerDuty messages.
12. **`temporal-ewma-worker`**: Periodically updates baseline cost gauges.
13. **`latency-baseline-worker`**: Calculates hourly baseline TTFT.

---

## Quick Start (Local Docker Compose)

Deploy the entire 13-service stack locally with a single script that automatically provisions database migrations and sets up daily backups:

```bash
# 1. Execute the main launcher script
./packages/configs/observability-deploy/scripts/deploy.sh
```

Choose **Option 2** from the interactive menu. Once started:
- **API Endpoint**: `http://localhost:8000`
- **Grafana Dashboards**: `http://localhost:3000` (Default credentials: `admin` / `admin`)
- **Prometheus UI**: `http://localhost:9090`
- **Temporal Web UI**: `http://localhost:8080`

---

## Deployment & Production Orchestration

We provide structured, multi-environment configurations under [`packages/configs/observability-deploy/deploy/`](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/):

### 1. Kubernetes Manifests (kubectl)
Located under [`deploy/kubernetes/`](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/kubernetes/):
- **Strict Isolation**: Integrates [network-policies.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/kubernetes/network-policies.yaml) to block unauthorized public ingress to stateful datastores.
- **Automated Startup Migrations**: Runs [migrations-job.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/kubernetes/migrations-job.yaml) on start to create Postgres and ClickHouse tables.
- **Automated Backups**: Runs [backup-cronjob.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/kubernetes/backup-cronjob.yaml) to backup databases daily.

Deploy to your active Kube context:
```bash
./packages/configs/observability-deploy/scripts/deploy.sh # Option 4
```

### 2. Cloud Infrastructure Provisioning (Terraform)
Located under [`deploy/terraform/`](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/terraform/):
- **AWS**: Custom VPC, EKS Cluster, RDS PostgreSQL, MSK Kafka, and ElastiCache Redis.
- **GCP**: VPC subnets, GKE Cluster, Cloud SQL Postgres, and MemoryStore Redis.
- **Azure**: VNet with Private Service connections, AKS Cluster, PostgreSQL Flexible Server, and Azure Cache for Redis.

Provision infrastructure:
```bash
./packages/configs/observability-deploy/scripts/deploy.sh # Options 5, 6, or 7
```

### 3. Remote Node Setup (Ansible)
Located under [`deploy/ansible/`](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/ansible/):
- Provisions dependencies on raw VM nodes.
- Installs Docker Engine and Compose.
- **Automates Firewall Isolation**: Enforces UFW rules denying public ports for Postgres (`5432`), Clickhouse (`8123`), Kafka (`9092`), and Redis (`6379`) while allowing HTTP (`8000`/`3000`).

To run Ansible playbooks:
```bash
./packages/configs/observability-deploy/scripts/deploy.sh # Option 8
```

---

## Database Backups & Zero-Downtime Migration

Refer to the [DATA_MIGRATION_AND_BACKUP.md](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/DATA_MIGRATION_AND_BACKUP.md) guide for details on data protection.

Manual backups can be run anytime:
```bash
./packages/configs/observability-deploy/scripts/backup.sh
```
Daily backups are automatically registered in the system crontab on local container startup.

---

## Hardware Resource Requirements

| Environment | Minimum CPU | Minimum RAM | Storage | Instance Type (Cloud) |
|---|---|---|---|---|
| **Local Dev** | 4 vCPUs | 12 GB | 30 GB SSD | Local Workstation |
| **Production** | 8 vCPUs | 32 GB | 100 GB+ SSD | 3x nodes (AWS `t3.large`, GCP `e2-standard-4`, Azure `Standard_D4s_v5`) |
