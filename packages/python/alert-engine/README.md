# Alert Engine Worker

Kafka consumer worker that processes and routes budget thresholds and cost anomaly alerts to PostgreSQL database history logs, Slack workspace channels, and PagerDuty endpoints.

---

## Why Use the Alert Engine?
- **Zero Spam (Deduplication)**: Suppresses duplicate alerts for the same `(user_id, model)` or `(service, model)` within a 15-minute rate-limiting window using Redis.
- **Dynamic Routing**:
  - **Budget Blocked**: Sent to a public `#llm-cost-alerts` Slack channel.
  - **Budget Warnings**: Looked up dynamically and sent as a direct Slack DM to the service owner.
  - **Cost Anomalies**: Triggers high-priority PagerDuty incidents (except during service cold-starts).
- **Persistent Logs**: Every dispatched alert is written to PostgreSQL for historical audits and analysis.
- **Traceability**: Out-of-the-box OpenTelemetry tracing propagation using the W3C standard.

---

## Architecture Dependencies
Ensure these services are available in your infrastructure environment:
1. **Kafka / Redpanda Broker**: Event stream source.
2. **Redis Cache (>= 6.0)**: Used for suppression / rate-limit locking.
3. **PostgreSQL Database (>= 12)**: Store target for the `alert_history` table.

---

## Kafka Configuration
Make sure the following topics are created on your Kafka broker before starting the engine:
* **`alerts.budget`**: Receives budget threshold event payloads.
* **`alerts.cost.anomaly`**: Receives cost anomaly event payloads.

*Default Consumer Group:* `alert-engine-group`

---

## Expected Results (Outputs)
Upon consuming events, the engine performs the following actions:
* Inserts a record into the PostgreSQL `alert_history` table:
  ```sql
  SELECT * FROM alert_history ORDER BY created_at DESC;
  ```
* Dispatches Slack notifications/DMs or triggers PagerDuty API calls.
* Exposes execution span telemetry metrics on port `9464`.

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

The alert engine is deeply instrumented with OpenTelemetry to track delivery latencies, database execution times, third-party notification overheads, and propagate distributed trace contexts across services.

### Tracing Instrumentation Hierarchy

The engine generates the following structured spans and sub-spans:
- **`budget_alert_handler.handle`** (Root span for budget alert processing)
  - Attributes: `alert.type`, `user_id`, `model`, `event_type`, `alert.suppressed`
  - Sub-spans:
    - `budget_alert_handler.check_rate_limit` (with `rate_limit.key` and `rate_limit.acquired`)
    - `budget_alert_handler.insert_database` (wrapping DB queries)
    - `budget_alert_handler.notify_slack_channel` / `budget_alert_handler.notify_slack_owner`
- **`cost_anomaly_alert_handler.handle`** (Root span for anomaly alert processing)
  - Attributes: `alert.type`, `service`, `model`, `sample_count`, `current_cost`, `ewma_value`, `alert.burn_ratio`
  - Sub-spans:
    - `cost_anomaly_alert_handler.insert_database`
    - `cost_anomaly_alert_handler.check_rate_limit`
    - `cost_anomaly_alert_handler.notify_slack`
    - `cost_anomaly_alert_handler.notify_pagerduty`
- **Adapters Spans**:
  - `postgres_adapter.insert_alert`: Captures Postgres storage queries.
  - `redis_adapter.acquire_rate_limit`: Tracks Redis rate limiting locks.
  - `slack_adapter.post`: Captures outgoing Slack webhook latency and channels.
  - `pagerduty_adapter.trigger_incident`: Tracks PagerDuty API calls.

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

---

---

## End-User Usage Guide

This section explains how developers and operators can configure, connect, and run this package either as a standalone container or programmatically in Python.

### 1. Infrastructure Connection Configuration (Environment Variables)

Configure the alert engine by supplying the following environment variables to your container or environment:

| Variable | Description | Default / Example Value |
| :--- | :--- | :--- |
| **`KAFKA_BOOTSTRAP_SERVERS`** | Host/port of Kafka brokers | `localhost:9099` (Default) |
| **`KAFKA_CONSUMER_GROUP`** | Kafka consumer group identifier | `alert-engine-group` |
| **`KAFKA_TOPICS`** | Comma-separated list of subscribed topics | `alerts.budget,alerts.cost.anomaly` |
| **`REDIS_URL`** | Redis connection URI for rate limiting | `redis://localhost:6389/0` |
| **`POSTGRES_DSN`** | Complete Postgres connection DSN (supercedes other variables if set) | `postgresql://user:pass@host:5439/db` |
| **`POSTGRES_HOST`** | Postgres server host address (fallback when DSN not set) | `localhost` (Default) |
| **`POSTGRES_PORT`** | Postgres server port (fallback when DSN not set) | `5439` (Default) |
| **`POSTGRES_USER`** | Postgres database username (fallback when DSN not set) | `postgres` (Default) |
| **`POSTGRES_PASSWORD`** | Postgres database password (fallback when DSN not set) | `postgres` (Default) |
| **`POSTGRES_DB`** | Postgres database name (fallback when DSN not set) | `ewma_db` (Default) |
| **`SLACK_WEBHOOK_URL`** | Webhook URL for Slack alerts | `http://localhost:8080/mock-slack` |
| **`PAGERDUTY_ROUTING_KEY`** | Integration key for PagerDuty | `mock-pagerduty-routing-key` |
| **`SERVICE_OWNERS_FILE_PATH`** | Path to service owners file | `service_owners.yaml` |
| **`PROMETHEUS_METRICS_PORT`** | Port for Prometheus metrics scraping | `9464` |
| **`HEALTH_CHECK_PORT`** | Port for health probes | `8001` |
| **`OTEL_EXPORTER_OTLP_ENDPOINT`**| OpenTelemetry trace collector endpoint | `http://localhost:4317` |
| **`OTEL_SERVICE_NAME`** | OpenTelemetry service identifier | `alert-engine` |

#### Run via Docker:
Run the container and expose health check (`8001`) and metrics (`9464`) ports:
```bash
docker run -d \
  --name alert-engine \
  -e KAFKA_BOOTSTRAP_SERVERS="kafka-host:9092" \
  -e REDIS_URL="redis://redis-host:6379/0" \
  -e POSTGRES_DSN="postgresql://postgres:postgres@db-host:5432/alert_db" \
  -e SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T00/B00/X00" \
  -e PAGERDUTY_ROUTING_KEY="pagerduty-key" \
  -e OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317" \
  -p 8001:8001 \
  -p 9464:9464 \
  chiefj/alert-engine:latest
```

---

### 2. Producing Kafka Alert Events (JSON Payloads)

#### Budget Alert Payload (`alerts.budget` topic)
```json
{
  "user_id": "user_12345",
  "model": "gpt-4-turbo",
  "event_type": "warning_80pct",
  "timestamp_utc": "2026-05-28T10:45:00Z"
}
```
*Note: Valid `event_type` options are `"blocked"` and `"warning_80pct"`.*

#### Cost Anomaly Alert Payload (`alerts.cost.anomaly` topic)
```json
{
  "service": "recommendation-service",
  "model": "claude-3-opus",
  "hour_of_week": 42,
  "current_cost": 150.50,
  "ewma_value": 30.10,
  "threshold_value": 90.30,
  "sample_count": 14,
  "timestamp": "2026-05-28T10:45:00Z",
  "is_cold_start": false,
  "cluster_drilldown": [
    {
      "cluster_id": "k8s-us-east-1",
      "cost": 120.40
    }
  ]
}
```

---

### 3. Service Owners Mapping (`service_owners.yaml`)
When a budget alert with `event_type="warning_80pct"` triggers, the system routes the Slack DM notification to the owner of the service using `service_owners.yaml`.
Configure this file in your workspace:
```yaml
service_owners:
  recommendation-service: "@john-doe"
  payment-processor: "@jane-smith"
  default: "@on-call-infra"
```

---

### 4. Programmatic Usage in Python
You can import the adapters, config loaders, and handlers directly in your Python application code.

#### Loading Configurations programmatically:
```python
from worker.config import load_config

# Automatically loads and validates config from environment variables
config = load_config()
print(f"Connecting to Kafka at {config.kafka_bootstrap_servers}")
```

#### Triggering Handlers manually:
```python
from src.infra.adapters.postgres.postgres_adapter import PostgresAdapter
from src.infra.adapters.redis.redis_adapter import RedisAdapter
from src.infra.adapters.slack.slack_adapter import SlackAdapter
from src.infra.adapters.metrics.prometheus_adapter import PrometheusAdapter
from src.handlers.alerts_budget.handler import BudgetAlertHandler

# Initialize the adapter ports
db_port = PostgresAdapter("postgresql://postgres:postgres@localhost:5432/alert_db")
redis_port = RedisAdapter("redis://localhost:6379/0")
slack_port = SlackAdapter("https://hooks.slack.com/services/T00/B00/X00")
metrics_port = PrometheusAdapter()

# Initialize the handler
budget_handler = BudgetAlertHandler(
    db_port=db_port,
    redis_port=redis_port,
    slack_port=slack_port,
    metrics_port=metrics_port,
    service_owners_path="service_owners.yaml"
)

# Process budget alert payload manually
budget_handler.handle({
    "user_id": "user_12345",
    "model": "gpt-4",
    "event_type": "blocked",
    "service": "recommendation-service",
    "timestamp_utc": "2026-05-28T10:45:00Z"
})
```


