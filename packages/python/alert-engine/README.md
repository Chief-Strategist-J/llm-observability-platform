# Alert Engine Worker

Kafka consumer worker that processes and routes budget thresholds and cost anomaly alerts to PostgreSQL database history logs, Slack workspace channels, and PagerDuty endpoints.

---

## Folder Structure

```
.
├── build/
│   └── Dockerfile
├── contracts/
│   └── events/
│       ├── alerts.budget.yaml
│       └── alerts.cost.anomaly.yaml
├── database/
│   └── migrations/
│       ├── 0001_init.rollback.sql
│       ├── 0001_init.sql
│       └── schema.lock
├── deploy/
│   └── docker/
│       └── docker-compose.yaml
├── feature-registry.yaml
├── pyproject.toml
├── README.md
├── scripts/
│   ├── migrate.py
│   ├── migrate.sh
│   ├── run.sh
│   └── test.sh
├── src/
│   ├── handlers/
│   │   ├── alerts_budget/
│   │   │   └── handler.py
│   │   └── alerts_cost_anomaly/
│   │       └── handler.py
│   ├── infra/
│   │   └── adapters/
│   │       ├── metrics/
│   │       │   └── prometheus_adapter.py
│   │       ├── pagerduty/
│   │       │   └── pagerduty_adapter.py
│   │       ├── postgres/
│   │       │   └── postgres_adapter.py
│   │       ├── redis/
│   │       │   └── redis_adapter.py
│   │       └── slack/
│   │           └── slack_adapter.py
│   ├── shared/
│   │   └── ports/
│   │       ├── db_port.py
│   │       ├── metrics_port.py
│   │       ├── pagerduty_port.py
│   │       ├── redis_port.py
│   │       └── slack_port.py
│   └── worker/
│       ├── config.py
│       ├── index.py
│       └── registry.py
├── tests/
│   └── unit/
│       ├── test_budget_handler.py
│       ├── test_cost_anomaly_handler.py
│       ├── test_failures.py
│       └── test_tracing.py
├── worker-registry.yaml
└── service_owners.yaml
```

---

## Work Execution & Decision Flow

The following decision trees detail the routing and suppression rules for budget and cost anomaly events:

### 1. Budget Alerts Routing (`alerts.budget` topic)

```
[alerts.budget Event Consumed]
└── Rate Limit Check (Redis: rate_limit:budget_alert:{user_id}:{model})
    │
    │   ► RATIONALE: Dedups repeat alerts within a 15-minute (900s) window.
    │     If the rate limit key exists, processing is suppressed to prevent
    │     alert fatigue.
    │
    ├── Key Exists (Suppressed)
    │   └── Skip processing
    │
    └── Key Acquired (Proceed)
        ├── 1. Parse Delivery Latency (timestamp_utc vs now)
        ├── 2. Write to PostgreSQL (alert_history table)
        ├── 3. Emit Prometheus histogram latency metric
        └── 4. Notification Dispatch:
            ├── event_type = 'blocked'
            │   └── Slack message to #llm-cost-alerts channel
            └── event_type = 'warning_80pct'
                └── Lookup owner in service_owners.yaml & send Slack DM
```

### 2. Cost Anomaly Alerts Routing (`alerts.cost.anomaly` topic)

```
[alerts.cost.anomaly Event Consumed]
└── Check is_cold_start (payload is_cold_start OR sample_count < 7)
    │
    ├── is_cold_start = TRUE
    │   ├── 1. Write to PostgreSQL (alert_history table)
    │   └── 2. Log message only (Do NOT notify Slack/PagerDuty)
    │
    └── is_cold_start = FALSE
        └── Check Burn Ratio (current_cost / ewma_value)
            │
            ├── burn_ratio <= 3.0 (Normal Deviation)
            │   └── Skip notification
            │
            └── burn_ratio > 3.0 (Cost Spike detected)
                └── Rate Limit Check (Redis: rate_limit:cost_anomaly:{service}:{model})
                    │
                    │   ► RATIONALE: Suppresses repeat anomaly alerts within a
                    │     1-hour (3600s) window.
                    │
                    ├── Key Exists (Suppressed)
                    │   └── Skip notifications
                    │
                    └── Key Acquired (Proceed)
                        ├── 1. Write to PostgreSQL (alert_history table)
                        ├── 2. Emit Prometheus latency metrics (critical severity)
                        ├── 3. Send PagerDuty incident alert
                        └── 4. Send Slack alert with drill-down (top contributor cluster)
```

---

## Sequencing & Dependency Map

Dependencies must be initialized and started in the following order:

```
[Step 1: Core Infra] --------> [Step 2: Database Migration] ----> [Step 3: Verification] ----> [Step 4: Run Worker]
  • Postgres (5432)              • ./scripts/migrate.sh           • ./scripts/test.sh         • ./scripts/run.sh
  • Redis (6379)                   (Initializes DB schema           (Runs unit test             (Starts Kafka poll
  • Kafka (9092)                    and creates indexes)             assertions)                 consumer loop)
```

---

## Setup & Execution

### 1. Configure Environment
Create a virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Database Migrations
Apply PostgreSQL database schema migrations to setup the `alert_history` table:
```bash
./scripts/migrate.sh
```

### 3. Run Verification Tests
Verify all alerting policies, routing logic, and mocks:
```bash
./scripts/test.sh
```

### 4. Run the Worker
Start the consumer listening to the Kafka topics:
```bash
./scripts/run.sh
```

---

## Observability & Tracing

The alert engine is instrumented with OpenTelemetry to track delivery latencies and propagate distributed trace contexts across services.

### Environment Variables
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OTLP collector endpoint for traces (e.g. `http://localhost:4317`).
- `OTEL_SERVICE_NAME`: Set to `alert-engine` by default.

Traces are automatically propagated from incoming Kafka message header metadata using the W3C traceparent context standard.

---

## Docker Deployment

### Build the Image
To build the Docker image for local development or production releases:
```bash
docker build -f build/Dockerfile -t chiefj/alert-engine:latest .
```

### Deploy using Docker Compose
Orchestrate all dependent services (PostgreSQL, Redis, Kafka, Tempo/OTLP collector) along with the worker:
```bash
docker compose -f deploy/docker/docker-compose.yaml up -d
```
