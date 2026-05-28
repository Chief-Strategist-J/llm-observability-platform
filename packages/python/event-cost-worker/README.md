# Event Cost Worker

Kafka consumer worker that aggregates LLM span cost data into Redis Fenwick Trees and reconciles token budgets post-call.

---

## Folder Structure

```
.
├── build/
│   └── Dockerfile
├── contracts/
│   ├── events/
│   │   ├── llm_spans_raw.yaml
│   │   └── changelog.md
│   └── schema.lock
├── database/
│   ├── migrations/
│   │   ├── 0001_redis_schema.rollback.sql
│   │   └── 0001_redis_schema.sql
│   └── schema.lock
├── deploy/
│   └── docker/
│       └── docker-compose.yaml
├── feature-registry.yaml
├── pyproject.toml
├── README.md
├── scripts/
│   ├── deploy_docker.sh
│   ├── health-check.sh
│   ├── migrate.sh
│   ├── run.sh
│   └── test.sh
├── src/
│   ├── handlers/
│   │   └── llm_spans_raw/
│   │       ├── index.py
│   │       ├── handler.py
│   │       ├── types.py
│   │       └── tests/
│   │           ├── integration/
│   │           │   └── test_handler_redis.py
│   │           └── unit/
│   │               └── test_handler.py
│   ├── shared/
│   │   ├── contracts/
│   │   │   └── validator.py
│   │   ├── types/
│   │   │   └── cost_types.py
│   │   └── utils/
│   │       └── retry.py
│   └── worker/
│       ├── config.py
│       ├── index.py
│       └── registry.py
└── worker-registry.yaml
```

---

## Work Execution & Decision Flow

The following detailed decision tree outlines how the consumer aggregates span costs and reconciles budgets, with justification for each design choice:

```
[Span Message Consumed from Kafka]
└── traceparent header extracted (OTel Context)
    │
    │   ► RATIONALE: Integrates with global W3C tracing. Ensures that span cost calculation
    │     participates in the parent span trace without breaking propagation.
    │
    └── Idempotency Guard (Redis DEDUP_CHECK_LUA)
        │
        │   ► RATIONALE: SADD + EXPIRE Lua script runs atomically on Redis. 
        │     If span_id already in 'dedup:cost_engine' set, return 0 (Skip processing). 
        │     This prevents double-counting costs if Kafka re-delivers a batch.
        │
        ├── Duplicate Span Found
        │   └── Skip processing (No-op)
        │
        └── New Span Found
            └── Price Reconciliation (Tolerance Check)
                │
                │   ► RATIONALE: Validates span.cost_usd_micro against the baseline price 
                │     configured in model_price_versions.yaml. Tolerates ±2% deviations to 
                │     allow minor provider rounding variances while detecting pricing anomalies.
                │
                ├── Cost within ±2% of baseline
                │   └── Use span.cost_usd_micro directly
                │
                └── Cost deviates > 2% (Price Anomaly)
                    ├── Log WARNING event with trace context
                    └── Recalculate cost = (prompt_tokens * input_rate) + (completion_tokens * output_rate)
                        │
                        │   ► RATIONALE: Safeguards the analytical layer from compromised, corrupt, 
                        │     or erroneous span cost payloads by correcting the value before aggregating.
                        │
                └── Batch aggregate execution (process_batch):
                    │
                    ├── 1. Redis Pipeline Fenwick Tree Updates
                    │   │
                    │   │   ► RATIONALE: Updates 5 dimensions (org, project, service, model, user) 
                    │   │     across 4 windows (1h, 24h, 7d, 30d) = 20 Fenwick Trees per span. 
                    │   │     Using a non-transactional Redis pipeline avoids blockages while maintaining 
                    │   │     extremely high aggregation throughput.
                    │   │
                    │   └── Execute 20 Lua calls per span concurrently in Redis pipeline
                    │
                    ├── 2. Token Bucket Retro Deduction
                    │   │
                    │   │   ► RATIONALE: Token buckets deduct budget BEFORE LLM calls (in SDK). 
                    │   │     If the actual completion_tokens exceed the pre-estimated amount, the 
                    │   │     remaining deficit is retroactively deducted here to maintain budget parity.
                    │   │
                    │   └── Call TOKEN_BUCKET_DEDUCT_LUA script for org/project if deficit exists
                    │
                    └── 3. EWMA Baseline Reading (F-C-04)
                        │
                        │   ► RATIONALE: Reads the baseline cost from ewma:cost:{service}:{model}:{hour} 
                        │     and logs the ratio (cost / baseline) to enable real-time anomaly analysis.
                        │
                        └── Read EWMA value from Redis cache
```

If any step raises an unhandled exception:
```
[Processing Exception Raised]
└── Catch exception and start exponential backoff (with_retry)
    │
    │   ► RATIONALE: Protects against transient Redis connectivity blips by retrying 
    │     3 times with exponential backoff (100ms, 200ms, 400ms).
    │
    ├── Successful execution on retry
    │   └── Commit Kafka offset
    │
    └── All 3 retries failed (Dead Letter Queue)
        │
        │   ► RATIONALE: Routes raw span bytes to 'llm.spans.raw.dlq' Kafka topic. 
        │     This prevents transient failures from blocking ingestion queue head-of-line.
        │
        ├── Publish payload to DLQ topic
        └── Commit Kafka offset (Acknowledge progress)
```

---

## Sequencing & Dependency Map

To run the worker successfully, you MUST spin up and configure dependencies in the following strict order:

```
[Step 1: Docker Containers] ---> [Step 2: Configuration] ---> [Step 3: Redis Schema Validation] ---> [Step 4: Verification] ---> [Step 5: Start Worker]
  • Redis Cache (6379)             • Copy .env.example          • ./scripts/migrate.sh                • ./scripts/test.sh         • ./scripts/run.sh
  • Kafka & Zookeeper (9092)       • Set hosts & ports            (Validates Redis connectivity)        (Runs full unit/            (Starts polling
                                                                                                         integration tests)          Kafka spans raw topic)
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
Use the provided `docker-compose` to run Redis and Redpanda locally:
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

The database schema is managed via light-weight migration templates tracked under `database/migrations/` and verified using a `schema.lock` file.

### How it Works
Since the worker is Redis-only, there are no SQL migrations. The migration script validates Redis connectivity and confirms that the Redis instance conforms to the key schemas documented in `database/migrations/0001_redis_schema.sql`.

### Apply Migrations (UP)
To validate the database connectivity and print schema configurations, run:
```bash
./scripts/migrate.sh
```

### Rollback Migrations
Since Redis keys are dynamic, rollback is achieved by flushing the Redis DB (only do this on dedicated cost-engine instances) or deleting keys matching `fenwick:*`, `budget:tb:*`, and `dedup:*`.

---

## Running Verification & Worker

### 1. Run Tests
Verify configuration, domain handlers, and Redis integration behavior using the test script:
```bash
./scripts/test.sh
```

### 2. Run Worker
Start the Kafka consumer loop:
```bash
./scripts/run.sh
```

---

## Event Schema (Kafka Interface)

The worker consumes JSON-encoded events from the `llm.spans.raw` topic.

### Payload Schema
```json
{
  "span_id": "8a02a831-29e8-45e6-bd27-4c3a2ef9d0a1",
  "trace_id": "bfd0b678-4395-46ae-a235-901d1df36ef8",
  "service_name": "recommendation-service",
  "model": "gpt-4",
  "provider": "openai",
  "prompt_tokens": 120,
  "completion_tokens": 250,
  "cost_usd_micro": 11100,
  "price_version": "v1.0",
  "timestamp_utc": "2026-05-27T10:18:00Z",
  "user_id": "usr-9281",
  "org_id": "org-4412",
  "project_id": "proj-901",
  "estimated_tokens": 100
}
```

---

## Redis Query API (Aggregates Interface)

End users can read the compiled aggregates directly from Redis.

### 1. Retrieve Fenwick Tree Cumulative Cost
To query the Fenwick Tree aggregate for a service, read the Hash fields:
```bash
# Get all entries in the Fenwick Tree hash
redis-cli HGETALL "fenwick:service:1h:recommendation-service"
```

### 2. Inspect Token Bucket Balance
To inspect the remaining budget for an organization and project:
```bash
redis-cli GET "budget:tb:org-4412:proj-901"
```

### 3. Check Idempotency Cache
To verify if a span ID has been cached for deduplication:
```bash
redis-cli SISMEMBER "dedup:cost_engine" "8a02a831-29e8-45e6-bd27-4c3a2ef9d0a1"
```

---

## Prometheus Metrics & Observability

The `event-cost-worker` is instrumented with Prometheus-native counters and histograms exposed via an HTTP metrics server (default port `9090` or configured via `PROMETHEUS_METRICS_PORT`).

### Metrics Dictionary

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `cost_engine_span_processing_seconds` | Histogram | None | Total duration of Kafka message and batch processing. |
| `cost_engine_spans_processed_total` | Counter | `status` (`success`, `failure`) | Total number of spans aggregated. |
| `cost_engine_redis_pipeline_seconds` | Histogram | None | Latency of bulk Redis Pipeline execution. |
| `cost_engine_fenwick_update_seconds` | Histogram | None | Latency of the Fenwick Tree Lua updates. |
| `cost_engine_kafka_lag` | Gauge | `partition` | Real-time partition ingestion lag. |
| `cost_engine_dlq_events_total` | Counter | `reason` | Total events routed to Dead Letter Queue. |

