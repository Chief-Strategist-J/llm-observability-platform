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

## Quick Start

```bash
cd packages/python/event-cost-worker
pip install -e ".[dev]"
scripts/test.sh
```
