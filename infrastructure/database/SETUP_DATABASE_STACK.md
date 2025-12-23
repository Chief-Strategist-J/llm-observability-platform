# Database Stack Setup Guide

This guide details the Python-only infrastructure for managing 12 database services.

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Activate Virtual Environment
source /home/j/live/dinesh/llm-chatbot-python/.venv/bin/activate
```

### 2. Start Worker

Start the unified worker that handles all database workflows:

```bash
python infrastructure/database/start_all_workers.py
```

### 3. Trigger Database Setup

Open a new terminal, activate the venv, and run the commands below.

#### Individual Setup
```bash
python infrastructure/database/manage_databases.py --enable mongodb
python infrastructure/database/manage_databases.py --enable postgres
python infrastructure/database/manage_databases.py --enable redis
python infrastructure/database/manage_databases.py --enable neo4j
python infrastructure/database/manage_databases.py --enable qdrant
python infrastructure/database/manage_databases.py --enable minio
python infrastructure/database/manage_databases.py --enable clickhouse
python infrastructure/database/manage_databases.py --enable opensearch
python infrastructure/database/manage_databases.py --enable cassandra
python infrastructure/database/manage_databases.py --enable milvus
python infrastructure/database/manage_databases.py --enable weaviate
python infrastructure/database/manage_databases.py --enable chroma
```

#### Multiple Setup
```bash
python infrastructure/database/manage_databases.py --enable mongodb neo4j postgres
```

#### Setup All
```bash
python infrastructure/database/manage_databases.py --enable all
```

### 4. Cleanup/Teardown

Stop and remove all database containers:

```bash
python infrastructure/database/terminate_workflows.py
```

---

## 📊 Available Services

All services are accessible via HTTPS (self-signed certs) through Traefik.

| Service | URL | User | Password | Details |
|---------|-----|------|----------|---------|
| **MongoExpress** | [https://scaibu.mongoexpress](https://scaibu.mongoexpress) | `admin` | `MongoExpressPassword123!` | MongoDB UI |
| **PgAdmin** | [https://scaibu.pgadmin](https://scaibu.pgadmin) | `admin@scaibu.io` | `PgAdminPassword123!` | Postgres UI |
| **Neo4j** | [https://scaibu.neo4j](https://scaibu.neo4j) | `neo4j` | `Neo4jPassword123!` | Graph DB |
| **Redis Commander** | [https://scaibu.redis](https://scaibu.redis) | - | - | Redis UI |
| **Qdrant** | [https://scaibu.qdrant](https://scaibu.qdrant) | - | - | Vector DB UI |
| **MinIO Console** | [https://scaibu.minio-console](https://scaibu.minio-console) | `admin` | `MinioPassword123!` | S3 Compatible |
| **ClickHouse UI** | [https://scaibu.clickhouse-ui](https://scaibu.clickhouse-ui) | - | - | Analytical DB |
| **OpenSearch** | [https://scaibu.opensearch-dashboards](https://scaibu.opensearch-dashboards) | `admin` | `admin` | Search Engine |
| **Cassandra Web** | [https://scaibu.cassandra-web](https://scaibu.cassandra-web) | - | - | NoSQL UI |
| **Attu (Milvus)** | [https://scaibu.attu](https://scaibu.attu) | - | - | Milvus UI |
| **Weaviate** | [https://scaibu.weaviate](https://scaibu.weaviate) | - | - | Vector DB |
| **Chroma** | [https://scaibu.chroma](https://scaibu.chroma) | - | - | Vector DB |

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Worker Layer"
        START[start_all_workers.py] --> W1[Worker Process]
        W1 --> |Listens| Q[database-setup-queue]
    end

    subgraph "Trigger Layer"
        CLI[manage_databases.py] --> |Signal| Q
    end

    subgraph "Workflows"
        Q --> WF1[MongodbSetupWorkflow]
        Q --> WF2[Neo4jSetupWorkflow]
        Q --> WF3[PostgresSetupWorkflow]
        Q --> WFn[...Other Workflows]
    end
    
    subgraph "Activities"
        WF1 --> ACT1[Generate Certificates]
        WF1 --> ACT2[Update /etc/hosts]
        WF1 --> ACT3[Docker Compose Up]
        ACT2 --> |127.0.2.1| HOSTS[/etc/hosts]
    end
    
    subgraph "Docker Infrastructure (Traefik)"
        ACT3 --> C1[(MongoDB)]
        ACT3 --> C2[(Neo4j)]
        
        TR[Traefik Proxy] --> |Routes| C1
        TR --> |Routes| C2
        
        CLIENT[Browser/App] --> |https://scaibu.*| TR
    end
```

### Key Components

*   **Traefik**: Routes usage of `127.0.2.1` to correct containers using Docker labels.
*   **Temporal**: Orchestrates the setup, ensuring retries and correct ordering (Certs -> Hosts -> Docker).
*   **Infrastructure Code**:
    *   `database_definitions.py`: Central Source of Truth for IPs and Hostnames.
    *   `base_database_setup.py`: Standardizes Docker operations, logs, and tracing.

---

## ⚙️ Configuration Reference

**Central Config**: `infrastructure/database/shared/database_definitions.py`

| Service | Hostname(s) | Container IP |
|---------|-------------|--------------|
| **Postgres** | `scaibu.postgres`, `scaibu.pgadmin` | `172.29.0.10` |
| **MongoDB** | `scaibu.mongodb`, `scaibu.mongoexpress` | `172.29.0.20` |
| **Redis** | `scaibu.redis` | `172.29.0.30` |
| **Neo4j** | `scaibu.neo4j` | `172.29.0.40` |
| **Qdrant** | `scaibu.qdrant` | `172.29.0.50` |
| **MinIO** | `scaibu.minio`, `scaibu.minio-console` | `172.29.0.60` |
| **ClickHouse**| `scaibu.clickhouse`, `scaibu.clickhouse-ui` | `172.29.0.70` |
| **OpenSearch**| `scaibu.opensearch`, `scaibu.opensearch-dashboards`| `172.29.0.80` |
| **Cassandra** | `scaibu.cassandra`, `scaibu.cassandra-web` | `172.29.0.90` |
| **Milvus** | `scaibu.milvus`, `scaibu.attu` | `172.29.0.100` |
| **Weaviate** | `scaibu.weaviate` | `172.29.0.110` |
| **Chroma** | `scaibu.chroma` | `172.29.0.120` |

### Network

*   **Name**: `database-network`
*   **Subnet**: `172.29.0.0/16`
*   **Traefik Host IP**: `127.0.2.1`

---
