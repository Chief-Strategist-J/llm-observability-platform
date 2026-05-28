# Temporal EWMA Worker

Temporal worker package for scheduled EWMA baseline updates and cost anomaly detection.

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

The following detailed decision tree outlines how the hourly workflow updates baselines and flags anomalies, with justification for each design choice:

```
[Hourly Cron Trigger (0 * * * *)]
└── EwmaBaselineUpdate Workflow Starts
    │
    │   ► RATIONALE: Scheduled cron triggers workflow at off-peak hour intervals.
    │
    └── Activity: fetch_active_pairs()
        │
        │   ► RATIONALE: Scans ClickHouse log volumes for active (service, model) pairs 
        │     in the last 7 days. This filters out millions of historical combinations, 
        │     focusing computation ONLY on active traffic to minimize cost and execution time.
        │
        └── Loop over active (service, model) pairs concurrently:
            │
            │   ► RATIONALE: Temporal workflows run loops concurrently. Concurrency allows 
            │     thousands of pairs to be evaluated in parallel without blocking.
            │
            ├── Activity: get_baseline(service, model, hour_of_week)
            │   │
            │   │   ► RATIONALE: Reads the current baseline record from PostgreSQL. PostgreSQL is
            │   │     used here because it provides ACID compliance for historical baselines.
            │   │
            │   ├── Existing Baseline NOT found (Cold Start)
            │   │   ├── Activity: fetch_global_model_avg(model)
            │   │   │
            │   │   │   ► RATIONALE: Lacking historical service/model pairing, we seed the baseline
            │   │   │     using the global average cost for this specific model (e.g. gpt-4o) across 
            │   │   │     all services. This prevents false positive anomaly triggers during cold starts.
            │   │   │
            │   │   └── Seed EWMA baseline value = Global Model Average
            │   │
            │   └── Existing Baseline found (Warm Status)
            │       ├── Activity: fetch_cost_history(service, model, hour_of_week)
            │       │   │
            │       │   │   ► RATIONALE: Queries ClickHouse for the cost of the same hour_of_week (0-167)
            │       │   │     over the last 4 weeks. ClickHouse is selected here because column-oriented 
            │       │   │     storage allows ultra-fast aggregation of historical logs.
            │       │   │
            │       │   └── Fetch last 4 occurrences from ClickHouse
            │       └── Compute EWMA baseline value using α=0.1:
            │           EWMA_new = (1 - α) * EWMA_prev + α * Cost_current
            │
            ├── Activity: fetch_current_cost_1h(service, model)
            │
            ├── Activity: upsert_baseline(EwmaRecord)
            │   │
            │   │   ► RATIONALE: Persists the calculated baseline to PostgreSQL for persistent audit trail.
            │   │
            │   └── Persist updated baseline to PostgreSQL
            │
            ├── Write updated EWMA value to Redis Cache
            │   │
            │   │   ► RATIONALE: Anomaly-detection gateways on the ingestion path need ultra-low latency. 
            │   │     Redis caches the calculated baseline under: ewma:cost:{service}:{model}:{hour_of_week}
            │   │
            │   └── Key: ewma:cost:{service}:{model}:{hour_of_week}
            │
            └── Decision: Is Cost_current > (3 * EWMA_baseline)?
                │
                ├── YES (Anomaly Detected)
                │   ├── Activity: fetch_cost_by_cluster_1h(service, model)
                │   │   │
                │   │   │   ► RATIONALE: If cost spikes, we query ClickHouse to break down the cost 
                │   │   │     contributions by Kubernetes cluster/namespace to locate the root cause.
                │   │   │
                │   │   └── Get cluster drilldown metrics
                │   │
                │   └── Activity: publish_anomaly_alert(AnomalyPayload)
                │       │
                │       │   ► RATIONALE: Publishes to Kafka topic 'cost-anomaly-alerts'. Using Kafka 
                │       │     decouples anomaly detection from notification delivery (Slack, pager).
                │       │
                │       └── Emit alert JSON to Kafka topic
                │
                └── NO (Normal State)
                    └── Do nothing
```

---

## Sequencing & Dependency Map

To run the worker successfully, you MUST spin up and configure dependencies in the following strict order:

```
[Step 1: Docker Containers] ---> [Step 2: Configuration] ---> [Step 3: DB Migrations] ---> [Step 4: Verification] ---> [Step 5: Start Worker]
  • ClickHouse (8123)              • Copy .env.example          • ./scripts/migrate.sh       • ./scripts/test.sh         • ./scripts/run.sh
  • PostgreSQL (5432)              • Set hosts & ports            (Applies SQL schemas)        (Ensures integrations       (Starts polling
  • Redis Cache (6379)                                                                          and mock runs pass)         Temporal task queue)
  • Kafka & Zookeeper (9092)
  • Temporal Server (7233)
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

---

## Database Migrations Guide

The database schema is managed via light-weight migration scripts tracked under `database/migrations/` and verified using a `schema.lock` file.

### How it Works
The migration status is tracked inside `/database/migrations/schema.lock` containing the active version tag (e.g. `0001` or `0000`).

### Apply Migrations (UP)
To apply pending database schemas, run:
```bash
./scripts/migrate.sh up
```
This runs `0001_init.sql` against the configured PostgreSQL database and writes `0001` to `schema.lock`.

### Rollback Migrations
To revert schemas and return to baseline state, run:
```bash
./scripts/migrate.sh rollback
```
This executes the rollback SQL scripts and sets the `schema.lock` version to `0000`.

### Creating a New Migration
1. Add your SQL changes inside `database/migrations/` using a sequential identifier (e.g., `0002_add_index.sql` and `0002_add_index.rollback.sql`).
2. Update the transition mappings inside `scripts/migrate.py` to support applying and rolling back your new script file.

---

## Running Verification & Worker

### 1. Run Tests
Verify configuration, domain services, and workflow behavior using the test script:
```bash
./scripts/test.sh
```

### 2. Run Worker
Start the Temporal worker polling queue `ewma-tasks`:
```bash
./scripts/run.sh
```

---

## Remote Management API (REST) & Observability

The worker includes a FastAPI management layer (port 8000 in prod) and exposes Prometheus metrics.

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | GET | Check worker status and config. |
| `/trigger` | POST | Trigger the EWMA baseline update workflow on-demand. |
| `/metrics` | GET | Exposes Prometheus metrics (integrity mismatch counts, price corrections). |

### Example Triggering EWMA Workflow

```bash
curl -X POST http://localhost:8000/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "force_hour": 42
  }'
```

---

## Weekly Integrity & Retroactive Price Correction Workflows

In addition to the hourly EWMA baseline updates, the worker hosts two high-reliability admin workflows:

### 1. Weekly Integrity Check Workflow (`WeeklyIntegrityCheck`)
Reconciles fast-path Redis Fenwick tree aggregates against the source-of-truth logs in ClickHouse across three key dimensions: `service`, `model`, and `user`.
*   **Threshold Validation**: If cumulative drift between Redis aggregates and ClickHouse counts exceeds a **1% tolerance limit**, it logs Prometheus mismatch metrics.
*   **Decoupled Alerting**: Publishes detailed drift payloads to Kafka for downstream paging and notification routing.

### 2. Retroactive Price Correction Workflow (`RetroactivePriceCorrection`)
Corrects historical span pricing in a robust "fix-forward" pattern when base model pricing is updated.
*   **Config Hot-Reloading**: Automatically loads updated pricing YAML configurations from the environment-configured path.
*   **Bulk Calculation**: Scans historical window spans, compares the span pricing version against the current target, and computes microsecond-precision cost deltas.
*   **Adjustment Records**: Inserts new correction records directly into ClickHouse to adjust cumulative metrics without altering historical raw logs.


