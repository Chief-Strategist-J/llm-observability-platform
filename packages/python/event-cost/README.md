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
│   ├── 0002-asynchronous-kafka-event-cost-processing-and-persistence.md
│   ├── 0003-consolidation-of-event-cost-client-and-worker-packages.md
│   └── README.md
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
│   ├── __init__.py
│   ├── features/
│   │   └── cost_ledger/
│   │       ├── backends/
│   │       ├── prices/
│   │       └── ledger.py
│   ├── handlers/
│   │   └── llm_spans_raw/
│   │       ├── handler.py
│   │       ├── index.py
│   │       └── types.py
│   ├── infra/
│   │   └── adapters/
│   │       └── metrics/
│   │           └── prometheus_adapter.py
│   ├── shared/
│   │   ├── contracts/
│   │   │   └── validator.py
│   │   ├── ports/
│   │   │   └── metrics_port.py
│   │   ├── types/
│   │   │   └── cost_types.py
│   │   └── utils/
│   │       └── retry.py
│   └── worker/
│       ├── config.py
│       ├── index.py
│       └── registry.py
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
from features.cost_ledger.ledger import CostLedger

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
from features.cost_ledger.ledger import CostLedger
from features.cost_ledger.backends.redis import RedisBackend

ledger = CostLedger(backend=RedisBackend(redis_url="redis://localhost:6379/0"))
```

> [!NOTE]
> **Redis Backend Windowing (v0.1):** In the current version, the Redis backend acts as a cumulative all-time cost counter, and the `window` parameter is ignored. Precise time-windowed queries are coming in v0.2. Use the default `SQLiteBackend` for exact time-windowed queries.

---

## Kafka Worker

### Setup & Running

#### 1. Prerequisites
- Python 3.10+
- Docker & Docker Compose

#### 2. Configure Virtual Environment & Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

#### 3. Run Tests
```bash
./scripts/test.sh
```

#### 4. Run Worker
```bash
./scripts/run.sh
```
