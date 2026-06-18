# `slo-burn-worker`

> **Temporal-based scheduled microservice** for computing multi-window SLO error-budget burn rates, routing deduplication-aware alerts, and publishing enriched events to Kafka.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Workflow Steps](#workflow-steps)
4. [Alert Routing Logic](#alert-routing-logic)
5. [Port / Adapter Map](#port--adapter-map)
6. [Configuration Reference](#configuration-reference)
7. [Directory Structure](#directory-structure)
8. [Local Development](#local-development)
9. [Docker](#docker)
10. [CI Pipeline](#ci-pipeline)
11. [Observability](#observability)

---

## Overview

The **SLO Burn Rate Worker** is a Temporal-scheduled Python service that runs every **60 seconds** (using a precise `ScheduleIntervalSpec` rather than cron to guarantee drift-free intervals). It evaluates latency SLO compliance across all active `(model, endpoint)` pairs seen in the last 6 hours and fires tiered alerts — **page / slack / ticket** — with deduplication backed by Redis TTL locks.

| Dimension | Value |
|---|---|
| **Runtime** | Python 3.11 / 3.12 |
| **Orchestrator** | Temporal (`slo-burn-rate-schedule`, every 60 s) |
| **Cache** | Redis (burn-rate state + dedup locks + DDSketch P95/P99) |
| **OLAP** | ClickHouse (`latency_checkpoints`, `llm_spans`) |
| **Messaging** | Kafka topic `alerts.latency.slo` |
| **Metrics** | Prometheus via `/metrics` on port 8000 |
| **Tracing** | OpenTelemetry + Temporal `TracingInterceptor` |

---

## Architecture

```
┌────────────────── Temporal Schedule (every 60 s) ──────────────────┐
│                                                                      │
│  SloBurnWorkflow                                                     │
│   ├─ Activity: fetch_active_pairs      ──► Redis SCAN slo:total:*   │
│   ├─ Activity: compute_burn_rates      ──► Redis MGET (5m/1h/6h)    │
│   ├─ Activity: write_burn_rates        ──► Redis SET burn_rate:*     │
│   └─ Activity: handle_alerts           ──► Redis SETNX dedup lock   │
│                                             ClickHouse baseline      │
│                                             Kafka produce            │
│                                             Prometheus counter       │
└──────────────────────────────────────────────────────────────────────┘
         │
         ▼
   FastAPI health/metrics server (port 8000)
```

---

## Workflow Steps

### 1 · Active Pair Identification (`fetch_active_pairs`)

Scans Redis for keys matching `slo:total:{model}:{endpoint}:{bucket}` written in the last 6 hours and extracts unique `(model, endpoint)` pairs.

### 2 · Burn Rate Computation (`compute_burn_rates`) — F-L-07

For each pair, reads three rolling windows from Redis bucket keys:

| Window | Keys read | Formula |
|--------|-----------|---------|
| **Fast (5 m)** | `now_bucket-5 … now_bucket-1` | `total_errors / total_requests` |
| **Medium (1 h)** | `now_bucket-60 … now_bucket-1` | same |
| **Slow (6 h)** | `now_bucket-360 … now_bucket-1` | same |

**Burn rate** = `error_rate / (1.0 − compliance_threshold)`

Compliance threshold defaults to `0.95` (configurable per model/endpoint via `slo_compliance_config.yaml`).

### 3 · Write Burn Rates (`write_burn_rates`)

Writes computed rates to Redis:

```
burn_rate:fast:{model}:{endpoint}    TTL = 300 s
burn_rate:medium:{model}:{endpoint}  TTL = 3600 s
burn_rate:slow:{model}:{endpoint}    TTL = 21600 s
```

### 4 · Alert Routing + Deduplication (`handle_alerts`) — F-L-08 / F-L-09

#### Routing Decision

| Severity | Condition |
|----------|-----------|
| `page` | `burn_rate_fast > 14.4` **AND** `burn_rate_medium > 6.0` |
| `slack` | `burn_rate_medium > 6.0` **AND** `burn_rate_slow > 3.0` (not page) |
| `ticket` | `burn_rate_slow > 1.0` (not page, not slack) |

#### Deduplication Lock Keys

```
rate_limit:latency_alert:{model}:{endpoint}:{severity}
```

| Severity | TTL |
|----------|-----|
| `page` | 15 min (900 s) |
| `slack` | 1 h (3 600 s) |
| `ticket` | 24 h (86 400 s) |

### 5 · Alert Enrichment & Publishing

Each alert published to Kafka `alerts.latency.slo` includes:

- P95 / P99 latency quantiles (from DDSketch in Redis)
- 7-day baseline P95 from ClickHouse `latency_checkpoints` (falls back to raw `llm_spans` aggregation)
- Remaining 30-day error budget percentage

---

## Port / Adapter Map

| Port | Vendor | Adapter |
|------|--------|---------|
| Temporal Worker | `temporalio` | `src/worker/index.py::Worker` |
| Redis SLO Reader | Redis | `src/infra/adapters/redis/redis_adapter.py::RedisAdapter` |
| ClickHouse Baseline | ClickHouse | `src/infra/adapters/clickhouse/clickhouse_adapter.py::ClickHouseAdapter` |
| Kafka Alert Producer | Confluent Kafka | `src/infra/adapters/kafka/kafka_alert_adapter.py::KafkaAlertAdapter` |
| Prometheus Metrics | Prometheus | `src/infra/adapters/metrics/prometheus_adapter.py::PrometheusAdapter` |

See [`.port-registry`](.port-registry) for the machine-readable port registry.

---

## Configuration Reference

All settings are read from environment variables (see [`.env.example`](.env.example)):

| Variable | Default | Description |
|----------|---------|-------------|
| `TEMPORAL_HOST` | `localhost:7239` | Temporal frontend gRPC address |
| `TEMPORAL_NAMESPACE` | `default` | Temporal namespace |
| `TEMPORAL_TASK_QUEUE` | `slo-burn-tasks` | Task queue name |
| `CLICKHOUSE_HOST` | `localhost` | ClickHouse host |
| `CLICKHOUSE_PORT` | `8129` | ClickHouse HTTP port |
| `CLICKHOUSE_USERNAME` | `default` | ClickHouse username |
| `CLICKHOUSE_PASSWORD` | _(empty)_ | ClickHouse password |
| `CLICKHOUSE_DATABASE` | `default` | ClickHouse database |
| `REDIS_URL` | `redis://localhost:6389/0` | Redis connection URL |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9099` | Kafka bootstrap servers |
| `SLO_COMPLIANCE_CONFIG_PATH` | `slo_compliance_config.yaml` | Per-model/endpoint thresholds |
| `DEFAULT_SLO_COMPLIANCE` | `0.95` | Fallback compliance target |

---

## Directory Structure

```
slo-burn-worker/
├── build/
│   └── Dockerfile                   # Multi-stage production image
├── contracts/                        # Shared Pydantic schema contracts
├── deploy/
│   └── docker/
│       └── docker-compose.yaml       # Local dev stack (Temporal, Redis, Kafka, CH)
├── scripts/
│   ├── run.sh                        # Start the worker
│   ├── test.sh                       # Run unit tests
│   └── health-check.sh              # Probe /health endpoint
├── src/
│   ├── api/rest/v1/app.py           # FastAPI health + metrics endpoints
│   ├── infra/
│   │   └── adapters/
│   │       ├── clickhouse/           # ClickHouseAdapter
│   │       ├── kafka/                # KafkaAlertAdapter
│   │       ├── metrics/              # PrometheusAdapter
│   │       └── redis/                # RedisAdapter
│   └── worker/
│       ├── activities.py            # Temporal activity implementations
│       ├── config.py                # Pydantic settings loader
│       ├── index.py                 # Entrypoint — wires everything up
│       ├── registry.py              # Worker-level service registry
│       └── workflows.py             # SloBurnWorkflow definition
├── tests/
│   └── unit/
│       ├── test_slo_service.py      # Service-layer unit tests
│       └── test_workflow.py         # Workflow/activity unit tests
├── .env.example
├── .port-registry
├── pyproject.toml
└── worker-registry.yaml
```

---

## Local Development

### Prerequisites

- Python 3.11+
- [Temporal CLI](https://docs.temporal.io/cli) for running a local Temporal server
- Docker (for full stack)

### Install

```bash
cd packages/python/slo-burn-worker
pip install -e ".[dev]"
```

### Run

```bash
# Start Temporal dev server (separate terminal)
temporal server start-dev --port 7239

# Start the worker
./scripts/run.sh
```

### Test

```bash
./scripts/test.sh
```

### Type check + Lint

```bash
mypy src/ --ignore-missing-imports --strict
ruff check src/ tests/
```

### Health check

```bash
./scripts/health-check.sh
# or manually:
curl http://localhost:8000/health
```

---

## Docker

### Build

```bash
docker build \
  -f packages/python/slo-burn-worker/build/Dockerfile \
  -t chiefj/slo-burn-worker:latest \
  packages/python/slo-burn-worker
```

### Run (standalone)

```bash
docker run --env-file packages/python/slo-burn-worker/.env.example \
  -p 8000:8000 \
  chiefj/slo-burn-worker:latest
```

### Full stack with Docker Compose

```bash
cd packages/python/slo-burn-worker/deploy/docker
docker compose up -d
```

### Published image

```
docker pull chiefj/slo-burn-worker:latest
```

---

## CI Pipeline

The workflow at [`.github/workflows/slo-burn-worker-test.yml`](/.github/workflows/slo-burn-worker-test.yml) runs on every push to `main` or `feature/slo-burn-worker`, and on all pull requests targeting `main`.

| Job | Steps |
|-----|-------|
| `test (3.11)` | Ruff lint → Mypy strict → pytest (≥70% coverage) |
| `test (3.12)` | Ruff lint → Mypy strict → pytest + coverage artifact upload |

---

## Observability

| Signal | Implementation |
|--------|---------------|
| **Traces** | `opentelemetry-sdk` + Temporal `TracingInterceptor` — spans on every activity call and every adapter network operation |
| **Metrics** | `prometheus-client` — counters/histograms exposed at `GET /metrics` |
| **Logs** | `logging` stdlib — structured at `INFO` level, configurable via env |
| **Health** | `GET /health` returns `{"status": "ok"}` |
