# Alert Engine (Kafka Consumer Worker)

The `alert-engine` is a decoupled microservice designed to consume budget thresholds and cost anomaly events from Kafka, write historical records to PostgreSQL, and route notifications to Slack and PagerDuty.

It runs a Kafka consumer poll loop that processes incoming events with OpenTelemetry context propagation and rate-limiting controls.

---

## Alert Routing & Verification Flow

### 1. Budget Alerts (`alerts.budget` topic)
- **Suppression**: Redis-based rate limiting prevents alert fatigue by suppressing repeat budget alerts for the same `(user_id, model)` within 15 minutes (900 seconds).
- **Storage**: All alerts write to PostgreSQL `alert_history` table.
- **Routing**:
  - `event_type = 'blocked'`: Slack notification to `#llm-cost-alerts` channel.
  - `event_type = 'warning_80pct'`: Looks up the service owner in `service_owners.yaml` and sends a direct message on Slack.

### 2. Cost Anomaly Alerts (`alerts.cost.anomaly` topic)
- **Cold Start Check**: If `is_cold_start = true` or `sample_count < 7`, the event is logged only and suppressed from notifications.
- **Burn Ratio Threshold**: Alerts are triggered only when `burn_ratio > 3.0`.
- **Suppression**: Redis-based rate limiting suppresses repeat cost anomaly alerts for the same `(service, model)` within 1 hour (3600 seconds).
- **Routing**: Sends a critical incident alert to PagerDuty and a detailed breakdown alert to Slack.

---

## OpenTelemetry Tracing Context Propagation

The worker extracts W3C traceparent headers from incoming Kafka headers. This ensures that processing actions and alert dispatches are correlated directly as child spans of the original client LLM request, preserving end-to-end tracing.

---

## Standalone Setup & Execution

An end-user can install and run this package individually by following these steps:

### 1. Install the package and dependencies:
```bash
pip install -e packages/python/alert-engine
```

### 2. Spin up local infrastructure:
This runs PostgreSQL, Redis, and Kafka:
```bash
docker compose -f packages/python/alert-engine/deploy/docker/docker-compose.yaml up -d
```

### 3. Configure the environment:
```bash
cp packages/python/alert-engine/.env.example packages/python/alert-engine/.env
```

### 4. Apply database migrations:
Apply SQL migration schemas to PostgreSQL:
```bash
./packages/python/alert-engine/scripts/migrate.sh
```

### 5. Run test verification:
Verify configuration and end-to-end integration flows:
```bash
./packages/python/alert-engine/scripts/test.sh
```

### 6. Start the Kafka Consumer Worker:
```bash
./packages/python/alert-engine/scripts/run.sh
```

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
