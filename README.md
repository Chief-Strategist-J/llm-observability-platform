# 🚀 LLM Observability Platform - Production Deployment Suite

> **Stop paying thousands of dollars to SaaS observability vendors. Claim complete data sovereignty, eliminate external telemetry leaks, and deploy a hardened 13-service observability pipeline in minutes.**

The LLM Observability Platform Deployment Suite is a unified, production-grade, self-hosted infrastructure orchestrator. Whether you are running a lightweight proof-of-concept on a local VM or scaling high-throughput LLM workloads across multi-cloud clusters, this suite provides robust, automated configurations to manage, secure, and monitor your pipelines with zero-lock-in.

---

## 🏆 Key Architectural Benefits

- **🔒 Hardened Zero-Trust Security**: Pre-configured Kubernetes NetworkPolicies and Ansible UFW firewalls isolate stateful data tiers (Postgres, ClickHouse, Redis) from public networks by default.
- **⚡ Automated Schema Migrations**: Zero-overhead database initialization. Containerized initialization jobs apply SQL schemas across Postgres and ClickHouse databases sequentially before core APIs start.
- **💾 Automatic Daily Backups**: Built-in automated cron generators. Installs system crontabs for Docker Compose or CronJobs in Kubernetes to backup and archive data at midnight.
- **📈 Multi-Cloud Scalability**: Provision enterprise-ready infra on AWS, GCP, and Azure using structured, cloud-specific Terraform subnets.

---

## 💻 Hardware Sizing Matrix

Choose the hardware allocation matching your operations load:

| Environment Tier | Target Load | Minimum CPU | Minimum RAM | Storage | Cloud Recommendations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **💡 Local Dev / VM** | Testing / Prototyping | 4 vCPUs | 12 GB | 30 GB SSD | Local Machine / Sandbox VM |
| **🚀 Production** | High-Throughput | 8 vCPUs | 32 GB | 100 GB+ SSD | 3x Nodes (AWS `t3.large`, GCP `e2-standard-4`, Azure `Standard_D4s_v5`) |

---

## ⚡ 1-Click Launch (Docker Compose)

Instantly spin up all **13 microservices and datastores** locally. The orchestrator script installs database migrations and backup scripts automatically:

```bash
# Start the interactive orchestration CLI
./packages/configs/observability-deploy/scripts/deploy.sh
```

Choose **Option 2** from the interactive menu. Once launched, access your self-hosted panels:
- 📥 **FastAPI Ingest API**: Port `8000` — High-performance ingestion endpoint.
- 📊 **Grafana Dashboard Console**: Port `3000` — Deep trace visualization graphs (Default: `admin` / `admin`).
- 📈 **Prometheus Metrics Engine**: Port `9090` — Scraping host and target health.
- ⏱️ **Temporal Web Interface**: Port `8080` — Tracking workflow cron states.

---

## 📦 Deployment & Production Orchestration

All deployment resources are organized inside the package [`packages/configs/observability-deploy/deploy/`](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/):

| Target Environment | Deployment Engine | Path / Directory | Core Configurations / Files | Premium Features |
| :--- | :--- | :--- | :--- | :--- |
| **Local Development** | Docker Compose | `deploy/docker/` | [docker-compose.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/docker/docker-compose.yaml) | Zero-setup, in-flight migrations, and automated host backup registration on startup. |
| **Kubernetes (EKS/GKE/AKS)** | kubectl | `deploy/kubernetes/` | [network-policies.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/kubernetes/network-policies.yaml)<br>[migrations-job.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/kubernetes/migrations-job.yaml)<br>[backup-cronjob.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/kubernetes/backup-cronjob.yaml) | Enforces strict pod-isolation boundaries, starts database schema Jobs, and schedules daily CronJob backups. |
| **AWS Cloud** | Terraform | `deploy/terraform/aws/` | [main.tf](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/terraform/aws/main.tf)<br>[variables.tf](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/terraform/aws/variables.tf) | Provisions isolated VPC networks, EKS Nodes, private RDS instances, and MSK Kafka brokers. |
| **GCP Cloud** | Terraform | `deploy/terraform/gcp/` | [main.tf](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/terraform/gcp/main.tf)<br>[variables.tf](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/terraform/gcp/variables.tf) | Provisions VPC subnets, GKE Cluster pools, private Cloud SQL DB, and MemoryStore Redis. |
| **Azure Cloud** | Terraform | `deploy/terraform/azure/` | [main.tf](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/terraform/azure/main.tf)<br>[variables.tf](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/terraform/azure/variables.tf) | Provisions private VNets, AKS clusters, PostgreSQL Flexible Servers, and Azure Cache Redis. |
| **Bare Metal / VMs** | Ansible | `deploy/ansible/` | [hosts.ini](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/ansible/hosts.ini)<br>[playbook.yaml](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/deploy/ansible/playbook.yaml) | Provisions VM nodes, installs Docker engines, and configures local UFW firewalls to deny database ports. |

> [!TIP]
> Run the orchestrator CLI tool to provision or deploy directly:
> ```bash
> ./packages/configs/observability-deploy/scripts/deploy.sh
> ```

---

## 💾 Database Backups & Zero-Downtime Migration

Refer to the [DATA_MIGRATION_AND_BACKUP.md](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/DATA_MIGRATION_AND_BACKUP.md) guide for details on data protection.

Manual backups can be run anytime:
```bash
./packages/configs/observability-deploy/scripts/backup.sh
```

---

## ⚖️ Benefits & Tradeoffs of the Self-Hosted Stack

| ✅ Benefits (Why Self-Host) | ⚠️ Tradeoffs & Considerations |
| :--- | :--- |
| **Full Data Sovereignty**: Ingested prompts, vectors, and PII data remain completely within your secure network boundaries. | **Operational Overhead**: Active monitoring is required to maintain health for ZooKeeper, Kafka, and ClickHouse clusters. |
| **High Cost Savings**: Zero pricing scaling constraints relative to commercial SaaS logging solutions. | **Resource Footprint**: Demands a minimum of 12 GB RAM locally to run python models and database engines concurrently. |
| **Strict Network Isolation**: Out-of-the-box Kubernetes NetworkPolicies and Ansible UFW firewalls secure stateful databases. | **Maintenance Responsibility**: DevOps teams own data lifecycle storage, backups management, and platform updates. |
| **Automated Lifecycle Ops**: Schema migrations and daily backup schedules are natively handled on startup. | **Cluster Complexity**: A 13-service microservices footprint requires robust container staging and network coordination. |
| **Resilient Workflow Engines**: Temporal orchestrates scorer logic and EWMA calculations with built-in retry-on-failure. | |
