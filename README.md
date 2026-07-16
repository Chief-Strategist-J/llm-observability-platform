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

- 📥 **FastAPI Ingest API**: [http://localhost:8000](http://localhost:8000)
- 📊 **Grafana Dashboards**: [http://localhost:3000](http://localhost:3000) (Credentials: `admin` / `admin`)
- 📈 **Prometheus UI**: [http://localhost:9090](http://localhost:9090)
- ⏱️ **Temporal Web Console**: [http://localhost:8080](http://localhost:8080)

---

## 📦 Deployment & Production Orchestration

All deployment resources are organized inside the package [`packages/configs/observability-deploy/deploy/`](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/):

### 🛡️ 1. Kubernetes Manifests (kubectl)
Located under [`deploy/kubernetes/`](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/kubernetes/):
- **🔒 Strict Isolation**: Enforces [network-policies.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/kubernetes/network-policies.yaml) denying public access to private datastores.
- **🔄 Automated Schema Migrations**: Runs [migrations-job.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/kubernetes/migrations-job.yaml) on start to initialize PostgreSQL and ClickHouse.
- **💾 Automated Backups**: Runs [backup-cronjob.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/kubernetes/backup-cronjob.yaml) daily.

> [!NOTE]
> Run the orchestrator tool to deploy directly to your active Kube context:
> ```bash
> ./packages/configs/observability-deploy/scripts/deploy.sh # Option 4
> ```

### ☁️ 2. Cloud Infrastructure Provisioning (Terraform)
Located under [`deploy/terraform/`](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/terraform/):
- **AWS**: Provisions custom VPC, EKS Cluster, RDS PostgreSQL, MSK Kafka, and ElastiCache Redis.
- **GCP**: Provisions VPC subnets, GKE Cluster, Cloud SQL Postgres, and MemoryStore Redis.
- **Azure**: Provisions secure VNet, AKS Cluster, PostgreSQL Flexible Server, and Azure Cache for Redis.

> [!IMPORTANT]
> Run the orchestrator tool to provision cloud resources:
> ```bash
> ./packages/configs/observability-deploy/scripts/deploy.sh # Options 5, 6, or 7
> ```

### ⚙️ 3. Remote Node Configuration (Ansible)
Located under [`deploy/ansible/`](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/ansible/):
- Installs Docker Engine and Compose on target VMs.
- **Firewall Isolation Rules**: Automatically configures local UFW firewalls blocking public access to database ports (`5432`, `8123`, `6379`, `9092`, `7233`).

> [!TIP]
> Run the orchestrator to configure remote nodes:
> ```bash
> ./packages/configs/observability-deploy/scripts/deploy.sh # Option 8
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
