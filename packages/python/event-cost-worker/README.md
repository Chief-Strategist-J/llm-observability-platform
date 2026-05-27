# Event Cost Worker

Kafka consumer worker that aggregates LLM span cost data into Redis Fenwick Trees and reconciles token budgets post-call.

## Architecture

```
llm.spans.raw (Kafka)
       │
       ▼
┌─────────────────────────┐
│   event-cost-worker     │
│                         │
│  ┌───────────────────┐  │
│  │ worker/index.py   │  │  ← Kafka consumer loop + DI wiring
│  │   ▼ poll batch    │  │
│  │   ▼ deserialize   │  │
│  │   ▼ retry(3x)     │  │
│  └───────┬───────────┘  │
│          ▼              │
│  ┌───────────────────┐  │
│  │ handlers/         │  │
│  │ llm_spans_raw/    │  │
│  │   handler.py      │  │  ← Pure domain logic (no I/O)
│  │   index.py        │  │  ← Thin orchestrator
│  └───────┬───────────┘  │
│          ▼              │
│  ┌───────────────────┐  │
│  │ Redis Adapters    │  │
│  │  Fenwick Trees    │  │  ← 5 dims × 4 windows = 20 Lua calls/span
│  │  Token Buckets    │  │  ← Retroactive delta deduction
│  │  EWMA Reader      │  │  ← Read-only burn ratio
│  └───────────────────┘  │
└─────────────────────────┘
       │ (on failure)
       ▼
llm.spans.raw.dlq (Kafka)
```

## Functional Requirements

| ID | Feature | Description |
|----|---------|-------------|
| F-C-01 | Fenwick Tree | 20 Redis Lua updates per span (5 dims × 4 windows), pipelined |
| F-C-02 | Token Bucket | Retroactive deduction when completion_tokens > estimated |
| F-C-03 | Price Reconciliation | ±2% tolerance check against model_price_versions |
| F-C-04 | EWMA Burn Ratio | Read ewma:cost:{service}:{model}:{hour} for logging |
| F-C-05 | Budget Events | Not produced here — SDK produces, alert-engine consumes |
| F-C-06 | Dead Letter | 3 retries (100ms/200ms/400ms), then DLQ + counter |

## Directory Structure

```
python/event-cost-worker/
├── contracts/events/
│   ├── llm_spans_raw.yaml
│   └── changelog.md
├── src/
│   ├── worker/
│   │   ├── config.py
│   │   ├── registry.py
│   │   └── index.py
│   ├── handlers/llm_spans_raw/
│   │   ├── index.py
│   │   ├── handler.py
│   │   ├── types.py
│   │   └── tests/unit/ + integration/
│   └── shared/
│       ├── types/cost_types.py
│       ├── utils/retry.py
│       └── contracts/validator.py
├── scripts/ (run.sh, test.sh, migrate.sh, health-check.sh)
├── build/Dockerfile
├── deploy/docker/docker-compose.yaml
├── pyproject.toml
├── worker-registry.yaml
└── feature-registry.yaml
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| KAFKA_BOOTSTRAP_SERVERS | localhost:9092 | Kafka broker addresses |
| KAFKA_CONSUMER_GROUP | event-cost-worker-group | Consumer group ID |
| KAFKA_TOPIC | llm.spans.raw | Source topic |
| KAFKA_DLQ_TOPIC | llm.spans.raw.dlq | Dead letter topic |
| REDIS_URL | redis://localhost:6379/0 | Redis connection |
| BATCH_SIZE | 500 | Spans per poll |
| MAX_RETRIES | 3 | Retry count before DLQ |
| RETRY_BASE_MS | 100 | Base backoff delay |
| PRICE_CONFIG_PATH | model_price_versions.yaml | Price lookup config |

## Redis Key Formats

| Key Pattern | Data Structure | Purpose |
|-------------|---------------|---------|
| `fenwick:{dim}:{window}:{key}` | Hash (Fenwick Tree) | Cost aggregation |
| `budget:tb:{org_id}:{project_id}` | String (counter) | Token budget tracking |
| `ewma:cost:{service}:{model}:{hour}` | String (float) | EWMA baseline (read-only) |

## Decision Logic Tree

The worker processes each span event according to the following decision flow:

```
                    Span Event Received (Kafka)
                               │
                               ▼
                    [Idempotency Check]
                               │
                       ┌───────┴───────┐
                 [Is Duplicate?]    [Is New?]
                       │               │
                       ▼               ▼
                    [Skip]     [Extract Tracing]
                                       │
                                       ▼
                             [Price Reconciliation]
                                       │
                               ┌───────┴───────┐
                         [Within ±2%?]    [Out of range?]
                               │               │
                               │               ▼
                               │        [Raise Warning]
                               ▼               │
                      [Calculate Cost] ◄───────┘
                               │
                               ▼
                   [Aggregate (Fenwick Trees)]
                               │
                               ▼
                  [Token Bucket Retro Deduction]
                               │
                               ▼
                    [Offset Committed]
```

If any step raises an unhandled exception:
```
                      Processing Span Error
                                │
                                ▼
                       [Retry (Max 3x)]
                                │
                         ┌──────┴──────┐
                  [Attempts < 3?]   [Attempts == 3?]
                         │                 │
                         ▼                 ▼
                [Exponential Backoff]   [Route to DLQ]
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

## End-to-End Testing Guide

### 1. Spin up Local Environment
Start Kafka (Redpanda) and Redis containers:
```bash
cd packages/python/event-cost-worker/deploy/docker
docker compose up -d
```

### 2. Start the Event Cost Worker
Set the configuration variables and run the worker script:
```bash
cd ../..
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export REDIS_URL="redis://localhost:6379/0"
export PRICE_CONFIG_PATH="src/handlers/llm_spans_raw/tests/unit/test_price_config.yaml"

python src/worker/index.py
```

### 3. Send a Mock Event via Redpanda CLI
In a separate terminal, use Redpanda's `rpk` command line inside the container to produce a mock span message:
```bash
docker exec -i docker-redpanda-1 rpk topic produce llm.spans.raw <<EOF
{"span_id": "8a02a831-29e8-45e6-bd27-4c3a2ef9d0a1", "trace_id": "bfd0b678-4395-46ae-a235-901d1df36ef8", "service_name": "recommendation-service", "model": "gpt-4", "provider": "openai", "prompt_tokens": 120, "completion_tokens": 250, "cost_usd_micro": 11100, "price_version": "v1.0", "timestamp_utc": "2026-05-27T10:18:00Z", "org_id": "org-4412", "project_id": "proj-901", "estimated_tokens": 100}
EOF
```

### 4. Verify Redis Aggregates
Check that the cost data has been aggregated correctly in Redis:
```bash
# Verify the Fenwick tree was updated
docker exec -it docker-redis-1 redis-cli HGETALL "fenwick:service:1h:recommendation-service"

# Verify idempotency key registration
docker exec -it docker-redis-1 redis-cli SISMEMBER "dedup:cost_engine" "8a02a831-29e8-45e6-bd27-4c3a2ef9d0a1"
```

### 5. Run the Local Test Suite
You can execute all local unit and integration tests with:
```bash
./scripts/test.sh
```

