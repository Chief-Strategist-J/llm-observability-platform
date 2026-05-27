# event-cost

Track LLM API costs in your Python app. No infrastructure required.

## Installation

```bash
pip install event-cost
```

## Quick Start (Zero Infrastructure)

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

Easily transition to the high-performance Redis adapter backing our production worker, sharing identical schema and metrics definitions:

```python
from event_cost import CostLedger
from event_cost.backends.redis import RedisBackend

ledger = CostLedger(backend=RedisBackend(redis_url="redis://localhost:6379/0"))
```

> [!NOTE]
> **Redis Backend Windowing (v0.1):** In the current version, the Redis backend acts as a cumulative all-time cost counter, and the `window` parameter is ignored. Precise time-windowed queries are coming in v0.2. Use the default `SQLiteBackend` for exact time-windowed queries.

## Running at Kafka Scale

Deploy the event-cost-worker for massive log volumes and asynchronous Kafka consumption:

```bash
docker pull chiefj/event-cost-worker:stable
```
