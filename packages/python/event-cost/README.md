# event-cost

Unified LLM API cost tracking package: client library + Kafka consumer worker.

- **Client Library** — `CostLedger` for recording and querying LLM costs (SQLite for local dev, Redis for production)
- **Kafka Worker** — consumes `llm.spans.raw` events, aggregates into Redis Fenwick Trees, reconciles token budgets

---

## Folder Structure

```
.
├── adr/
│   ├── 0001-micro-usd-cost-ledger-and-multi-backend-pricing-engine.md
│   └── 0002-asynchronous-kafka-event-cost-processing-and-persistence.md
├── build/
│   └── Dockerfile
├── contracts/
│   └── events/
│       ├── llm_spans_raw.yaml
│       └── changelog.md
├── database/
│   ├── migrations/
│   └── schema.lock
├── deploy/
│   └── docker/
│       └── docker-compose.yaml
├── examples/
│   ├── basic.py
│   ├── fastapi.py
│   └── with_redis.py
├── scripts/
│   ├── deploy_docker.sh
│   ├── health-check.sh
│   ├── migrate.sh
│   ├── run.sh
│   └── test.sh
├── src/
│   └── event_cost/
│       ├── __init__.py              # Public API: CostLedger, SpanInput
│       ├── ledger.py
│       ├── backends/
│       │   ├── _base.py
│       │   ├── redis.py
│       │   └── sqlite.py
│       ├── prices/
│       │   └── builtin.yaml
│       ├── shared/
│       │   ├── contracts/
│       │   │   └── validator.py
│       │   ├── ports/
│       │   │   └── metrics_port.py
│       │   ├── types/
│       │   │   └── cost_types.py
│       │   └── utils/
│       │       └── retry.py
│       ├── infra/
│       │   └── adapters/
│       │       └── metrics/
│       │           └── prometheus_adapter.py
│       ├── handlers/
│       │   └── llm_spans_raw/
│       │       ├── handler.py
│       │       ├── index.py
│       │       └── types.py
│       └── worker/
│           ├── config.py
│           ├── index.py
│           └── registry.py
├── tests/
│   ├── test_ledger.py
│   └── handlers/
│       └── llm_spans_raw/
│           ├── unit/
│           │   ├── test_handler.py
│           │   ├── test_health.py
│           │   └── test_metrics.py
│           └── integration/
│               └── test_handler_redis.py
├── feature-registry.yaml
├── model_price_versions.yaml
├── pyproject.toml
└── worker-registry.yaml
```

---

## Quick Start — Client Library (Zero Infrastructure)

By default, `event-cost` uses a lightweight, local SQLite database under `~/.event-cost/ledger.db` with builtin pricing models:

```python
from event_cost import CostLedger

ledger = CostLedger()

ledger.record(
    model="gpt-4",
    provider="openai",
    prompt_tokens=120,
    completion_tokens=250,
    org_id="my-org",
    project_id="my-project",
    service_name="chat-api",
    user_id="usr-1"
)

print(ledger.total_cost_usd(org_id="my-org", window="24h"))
```

## Scale Up (Redis Backend)

Easily transition to the high-performance Redis adapter:

```python
from event_cost import CostLedger
from event_cost.backends.redis import RedisBackend

ledger = CostLedger(backend=RedisBackend(redis_url="redis://localhost:6379/0"))
```

> [!NOTE]
> **Redis Backend Windowing (v0.1):** In the current version, the Redis backend acts as a cumulative all-time cost counter, and the `window` parameter is ignored. Precise time-windowed queries are coming in v0.2. Use the default `SQLiteBackend` for exact time-windowed queries.

---

## Kafka Worker

### Work Execution & Decision Flow

```
[Span Message Consumed from Kafka]
└── traceparent header extracted (OTel Context)
    └── Idempotency Guard (Redis DEDUP_CHECK_LUA)
        ├── Duplicate Span → Skip (No-op)
        └── New Span
            └── Price Reconciliation (±2% tolerance)
                └── Batch aggregate execution (process_batch):
                    ├── 1. Redis Pipeline Fenwick Tree Updates (20 trees per span)
                    ├── 2. Token Bucket Retro Deduction
                    └── 3. EWMA Baseline Reading + Burn Ratio Logging
```

### Setup & Running

#### 1. Prerequisites
- Python 3.11+
- Docker & Docker Compose

#### 2. Configure Virtual Environment & Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

#### 3. Spin Up Infrastructure
```bash
docker compose -f deploy/docker/docker-compose.yaml up -d
```

#### 4. Configure Environment Variables
```bash
cp .env.example .env
```

#### 5. Run Tests
```bash
./scripts/test.sh
```

#### 6. Run Worker
```bash
./scripts/run.sh
```

---

## Event Schema (Kafka Interface)

The worker consumes JSON-encoded events from the `llm.spans.raw` topic:

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

### Retrieve Fenwick Tree Cumulative Cost
```bash
redis-cli HGETALL "fenwick:service:1h:recommendation-service"
```

### Inspect Token Bucket Balance
```bash
redis-cli GET "budget:tb:org-4412:proj-901"
```

### Check Idempotency Cache
```bash
redis-cli SISMEMBER "dedup:cost_engine" "8a02a831-29e8-45e6-bd27-4c3a2ef9d0a1"
```

---

## Prometheus Metrics & Observability

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `cost_engine_spans_processed_total` | Counter | `service`, `model` | Total spans processed by cost engine. |
| `cost_engine_fenwick_update_latency_ms` | Histogram | None | Latency of Fenwick Tree updates. |
| `cost_engine_redis_pipeline_latency_ms` | Histogram | None | Latency of Redis pipeline execution. |
| `cost_engine_kafka_lag` | Gauge | `partition` | Real-time partition ingestion lag. |
| `cost_engine_dlq_total` | Counter | `reason` | Total events routed to Dead Letter Queue. |
