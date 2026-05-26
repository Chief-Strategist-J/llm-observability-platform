# Temporal EWMA Worker

Temporal worker package for scheduled EWMA baseline updates and cost anomaly detection.

## Architecture

This worker is built following the Ports and Adapters (Hexagonal) architecture:
- **Domain/Core**: Contains the pure EWMA computation logic and the deterministic workflow definition.
- **Ports**: Protocol definitions for dependencies (ClickHouse, Redis, Postgres, Kafka).
- **Adapters**: Concrete implementations for the databases and message bus.
- **Activities**: Functions executing actual side effects and I/O using the adapters.

## Features

- **F-C-07**: Per-(service, model, hour_of_week) EWMA updates.
- **F-C-08**: Anomaly checking (current cost > 3x EWMA baseline).
- **F-C-09**: Cold start seeding using model-wide average cost.

---

## Folder Structure

```
.
├── build/
│   └── Dockerfile
├── contracts/
│   ├── asyncapi/
│   │   └── v1.yaml
│   ├── changelog.md
│   └── workflows/
│       └── ewma_baseline_update.yaml
├── database/
│   ├── migrations/
│   │   ├── 0001_init.rollback.sql
│   │   └── 0001_init.sql
│   └── schema.lock
├── deploy/
│   └── docker/
│       └── docker-compose.yaml
├── feature-registry.yaml
├── pyproject.toml
├── README.md
├── scripts/
│   ├── deploy_docker.sh
│   ├── migrate.py
│   ├── migrate.sh
│   ├── run.sh
│   └── test.sh
├── src/
│   ├── features/
│   │   └── ewma_compute/
│   │       ├── index.py
│   │       └── service.py
│   ├── infra/
│   │   └── adapters/
│   │       ├── clickhouse/
│   │       │   └── clickhouse_adapter.py
│   │       ├── kafka/
│   │       │   └── kafka_alert_adapter.py
│   │       ├── postgres/
│   │       │   └── postgres_adapter.py
│   │       └── redis/
│   │           └── redis_adapter.py
│   ├── shared/
│   │   ├── contracts/
│   │   │   └── validator.py
│   │   ├── errors/
│   │   │   └── base.py
│   │   ├── ports/
│   │   │   ├── clickhouse_port.py
│   │   │   ├── postgres_port.py
│   │   │   └── redis_port.py
│   │   └── types/
│   │       └── ewma_types.py
│   └── worker/
│       ├── activities.py
│       ├── config.py
│       ├── index.py
│       ├── registry.py
│       └── workflows.py
├── tests/
│   ├── integration/
│   │   └── test_adapters.py
│   └── unit/
│       ├── test_config.py
│       ├── test_contract.py
│       ├── test_ewma_service.py
│       └── test_workflow.py
└── worker-registry.yaml
```

---

## Work Execution & Decision Flow

The following ASCII decision tree outlines how the hourly workflow updates baselines and flags anomalies:

```
[Hourly Cron Trigger (0 * * * *)]
└── EwmaBaselineUpdate Workflow Starts
    └── Activity: fetch_active_pairs()
        └── Loop over active (service, model) pairs concurrently:
            ├── Activity: get_baseline(service, model, hour_of_week)
            │   ├── Existing Baseline NOT found (Cold Start)
            │   │   ├── Activity: fetch_global_model_avg(model)
            │   │   └── Seed EWMA baseline value = Global Model Average
            │   │
            │   └── Existing Baseline found (Warm Status)
            │       ├── Activity: fetch_cost_history(service, model, hour_of_week)
            │       │   └── Fetch last 4 occurrences from ClickHouse
            │       └── Compute EWMA baseline value using α=0.1:
            │           EWMA_new = (1 - α) * EWMA_prev + α * Cost_current
            │
            ├── Activity: fetch_current_cost_1h(service, model)
            │
            ├── Activity: upsert_baseline(EwmaRecord)
            │   └── Persist updated baseline to PostgreSQL
            │
            ├── Write updated EWMA value to Redis Cache
            │   └── Key: ewma:cost:{service}:{model}:{hour_of_week}
            │
            └── Decision: Is Cost_current > (3 * EWMA_baseline)?
                ├── YES (Anomaly Detected)
                │   ├── Activity: fetch_cost_by_cluster_1h(service, model)
                │   └── Activity: publish_anomaly_alert(AnomalyPayload)
                │       └── Emit alert JSON to Kafka topic: cost-anomaly-alerts
                │
                └── NO (Normal State)
                    └── Do nothing
```

---

## Setup & Running

Follow these steps to set up the local development environment and run the worker:

### 1. Prerequisites
Ensure you have the following installed:
- Python 3.11+
- Docker & Docker Compose
- Git

### 2. Configure Virtual Environment & Dependencies
Create a virtual environment and install the package along with development requirements:
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install package in editable mode with development dependencies
pip install -e ".[dev]"
```

### 3. Spin Up Infrastructure
Use the provided `docker-compose` to run ClickingHouse, Postgres, Redis, Kafka, and Temporal locally:
```bash
docker compose -f deploy/docker/docker-compose.yaml up -d
```

### 4. Configure Environment Variables
Copy the template `.env.example` to `.env` and fill in custom connection strings if necessary:
```bash
cp .env.example .env
```

### 5. Run Database Migrations
Deploy PostgreSQL schemas using the migration utility:
```bash
./scripts/migrate.sh
```

### 6. Run Tests
Verify configuration, domain services, and workflow behavior using the test script:
```bash
./scripts/test.sh
```

### 7. Run Worker
Start the Temporal worker polling queue `ewma-tasks`:
```bash
./scripts/run.sh
```
