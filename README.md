# 🚀 LLM Observability Platform - Deployment Suite

This repository provides a unified, production-grade, and development-ready deployment layout for the **LLM Observability Platform** stack. It coordinates all **13 integrated services** (PostgreSQL, Redis, ClickHouse, ZooKeeper, Kafka, Temporal, and the FastAPI APIs / background scorer microservices) across local and cloud environments.

---

## 💻 Hardware Resource Requirements

Running the full suite of 13 services concurrently requires a baseline level of system resources due to the integration of stateful databases (ClickHouse, Postgres, Redis), Kafka, Temporal, and model inference workers.

| Environment | Minimum CPU | Minimum RAM | Storage | Instance Type (Cloud) |
| :--- | :--- | :--- | :--- | :--- |
| **Local Dev** | 4 vCPUs | 12 GB | 30 GB SSD | Local Workstation |
| **Production** | 8 vCPUs | 32 GB | 100 GB+ SSD | 3x nodes (AWS `t3.large`, GCP `e2-standard-4`, Azure `Standard_D4s_v5`) |

---

## 📋 Prerequisites

Ensure the following tools are installed locally based on your target environment:

- **Local Dev / VMs**: `docker` and `docker-compose`
- **Kubernetes**: `kubectl`
- **Cloud Infrastructure**: `terraform`
- **Remote VM provisioning**: `ansible-playbook`

---

## ⚡ Quick Start (Local Docker Compose)

Deploy the entire 13-service stack locally with a single script that automatically provisions database migrations and sets up daily backups:

```bash
# Execute the main orchestrator launcher script
./packages/configs/observability-deploy/scripts/deploy.sh
```

Choose **Option 2** from the interactive menu. Once started, you can access the system consoles:

- 📥 **FastAPI Ingest API**: Port `8000`
- 📊 **Grafana Dashboards**: Port `3000` (Default credentials: `admin` / `admin`)
- 📈 **Prometheus UI**: Port `9090`
- ⏱️ **Temporal Web Console**: Port `8080`

---

## 📦 Deployment & Production Orchestration

All deployment resources are organized inside the package [`packages/configs/observability-deploy/deploy/`](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/):

| Target Environment | Tool / Engine | Path / Directory | Core Configurations / Files | Features & Security |
| :--- | :--- | :--- | :--- | :--- |
| **Local Development** | Docker Compose | `deploy/docker/` | [docker-compose.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/docker/docker-compose.yaml) | Full 13-service stack startup orchestration, automated migrations, automated daily backups. |
| **Kubernetes (EKS/GKE/AKS)** | kubectl | `deploy/kubernetes/` | [network-policies.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/kubernetes/network-policies.yaml)<br>[migrations-job.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/kubernetes/migrations-job.yaml)<br>[backup-cronjob.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/kubernetes/backup-cronjob.yaml) | Strict NetworkPolicies, automated Postgres & ClickHouse startup migrations, daily CronJob backups. |
| **AWS Cloud** | Terraform | `deploy/terraform/aws/` | [main.tf](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/terraform/aws/main.tf)<br>[variables.tf](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/terraform/aws/variables.tf) | Custom VPC, EKS Cluster nodes, private RDS PostgreSQL instance, MSK Kafka broker, and ElastiCache. |
| **GCP Cloud** | Terraform | `deploy/terraform/gcp/` | [main.tf](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/terraform/gcp/main.tf)<br>[variables.tf](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/terraform/gcp/variables.tf) | Isolated subnets, GKE Cluster pool, Cloud SQL PostgreSQL, and MemoryStore Redis. |
| **Azure Cloud** | Terraform | `deploy/terraform/azure/` | [main.tf](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/terraform/azure/main.tf)<br>[variables.tf](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/terraform/azure/variables.tf) | Private VNet, AKS Cluster pool, Azure Database PostgreSQL (Flexible), and Azure Cache Redis. |
| **Bare Metal / VMs** | Ansible | `deploy/ansible/` | [hosts.ini](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/ansible/hosts.ini)<br>[playbook.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/ansible/playbook.yaml) | Node configuration, auto-installs Docker & Compose, configures UFW firewall rules denying public DB access. |

> [!TIP]
> Run the main orchestrator script to automatically trigger these configurations:
> ```bash
> ./packages/configs/observability-deploy/scripts/deploy.sh
> ```


---

## 💾 Database Backups & Migration Strategy

For zero-downtime data migration and backups, refer to the [DATA_MIGRATION_AND_BACKUP.md](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/DATA_MIGRATION_AND_BACKUP.md) guide.

To trigger backups manually at any time:
```bash
./packages/configs/observability-deploy/scripts/backup.sh
```

> [!WARNING]
> Daily automated backups are registered automatically in the user's host crontab when starting the Docker Compose local stack.

---

## ⚖️ Benefits & Tradeoffs of the Self-Hosted Stack

| ✅ Benefits (Why Self-Host) | ⚠️ Tradeoffs & Considerations |
| :--- | :--- |
| **Full Data Sovereignty**: Ingested prompts, vectors, and PII data remain completely within your secure network boundaries. | **Operational Overhead**: Active monitoring is required to maintain health for ZooKeeper, Kafka, and ClickHouse clusters. |
| **High Cost Savings**: Zero pricing scaling constraints relative to commercial SaaS logging solutions. | **Resource Footprint**: Demands a minimum of 12 GB RAM locally to run python models and database engines concurrently. |
| **Strict Network Isolation**: Out-of-the-box Kubernetes NetworkPolicies and Ansible UFW firewalls secure stateful databases. | **Maintenance Responsibility**: DevOps teams own data lifecycle storage, backups management, and platform updates. |
| **Automated Lifecycle Ops**: Schema migrations and daily backup schedules are natively handled on startup. | **Cluster Complexity**: A 13-service microservices footprint requires robust container staging and network coordination. |
| **Resilient Workflow Engines**: Temporal orchestrates scorer logic and EWMA calculations with built-in retry-on-failure. | |


