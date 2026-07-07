# Forecast Worker — `chiefj/forecast-worker`

> **Proactive LLM cost intelligence powered by [Google TimesFM](https://github.com/google-research/timesfm).  
> Pairs with `chiefj/instrumentation-sdk-api` to deliver live forecast graphs in Grafana.**

---

## Table of Contents

1. [What This Package Does](#1-what-this-package-does)
2. [How the Two Images Work Together](#2-how-the-two-images-work-together)
3. [Quick Start (Docker — End User)](#3-quick-start-docker--end-user)
4. [Sending Forecast Data from Your App](#4-sending-forecast-data-from-your-app)
5. [Viewing Forecasts in Grafana](#5-viewing-forecasts-in-grafana)
6. [Core Architectural Pipeline](#6-core-architectural-pipeline)
7. [Model Parameters and Caching](#7-model-parameters-and-caching)
8. [Database Migrations](#8-database-migrations)
9. [Folder Structure](#9-folder-structure)
10. [Development and Testing](#10-development-and-testing)

---

## 1. What This Package Does

The **Forecast Worker** is a Temporal-based cron worker that solves proactive cost and latency tracking using **Google TimesFM (Time Series Forecasting Model)**.

Unlike EWMA (Exponentially Weighted Moving Average) — which is *reactive* and only alerts after a budget spike or SLO breach — the Forecast Worker is **proactive**. It:

1. Aggregates historical cost/token logs from ClickHouse (last 168 hours).
2. Runs **TimesFM inference** to project the trend **24 hours into the future**.
3. Produces three quantile outputs: **mean**, **p10** (optimistic), **p90** (pessimistic).
4. Pushes results to the **Instrumentation SDK API** via HTTP — which exposes them as Prometheus metrics visible in Grafana dashboards.

---

## 2. How the Two Images Work Together

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         YOUR APPLICATION STACK                              │
│                                                                             │
│  ┌──────────────────────────────┐    ┌──────────────────────────────────┐  │
│  │   chiefj/forecast-worker     │    │  chiefj/instrumentation-sdk-api  │  │
│  │                              │    │                                  │  │
│  │  ┌──────────────────────┐    │    │  ┌────────────────────────────┐  │  │
│  │  │ Temporal Cron Worker │    │    │  │ FastAPI (port 8000)        │  │  │
│  │  │ Runs every 5 minutes │    │    │  │  POST /v1/metrics/forecast │  │  │
│  │  └──────────┬───────────┘    │    │  │  POST /v1/metrics/record   │  │  │
│  │             │                │    │  │  GET  /v1/metrics/health   │  │  │
│  │  ┌──────────▼───────────┐    │    │  └────────────┬───────────────┘  │  │
│  │  │  TimesFM Inference   │    │    │               │                  │  │
│  │  │  (google/timesfm-    │    │    │  ┌────────────▼───────────────┐  │  │
│  │  │   2.5-200m-pytorch)  │    │    │  │ OTel Prometheus Adapter   │  │  │
│  │  └──────────┬───────────┘    │    │  │ Observable Gauges (p/s)   │  │  │
│  │             │                │    │  └────────────┬───────────────┘  │  │
│  │  ┌──────────▼───────────┐    │    │               │                  │  │
│  │  │  Quantile Output     │    │    │  ┌────────────▼───────────────┐  │  │
│  │  │  mean / p10 / p90    ├────┼────►  │ Prometheus Exporter :9464 │  │  │
│  │  └──────────────────────┘    │    │  └────────────┬───────────────┘  │  │
│  │                              │    │               │                  │  │
│  │  Your app also calls SDK     │    │  ┌────────────▼───────────────┐  │  │
│  │  directly for span metrics   │    │  │ Prometheus  :9090          │  │  │
│  └──────────────────────────────┘    │  └────────────┬───────────────┘  │  │
│                                      │               │                  │  │
│  ┌───────────────────────────────────┼───────────────▼───────────────┐  │  │
│  │               Grafana :3000       │   Dashboards auto-provisioned │  │  │
│  │  ┌────────────────────────────────┼──────────────────────────────┐│  │  │
│  │  │  LLM Cost Forecast Dashboard  │  Mean/p10/p90 time-series    ││  │  │
│  │  │  LLM Cost Dashboard           │  Actual vs Forecast overlay  ││  │  │
│  │  │  LLM Security Dashboard       │  PII / Injection events      ││  │  │
│  │  └────────────────────────────────┴──────────────────────────────┘│  │  │
│  └───────────────────────────────────────────────────────────────────┘  │  │
│                                      └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Step-by-Step

| Step | Component | What Happens |
|------|-----------|--------------|
| **1** | Your App | Calls `POST /v1/metrics/record` with span data (tokens, cost, latency) |
| **2** | `instrumentation-sdk-api` | Records OTel counters/histograms → exported to Prometheus port 9464 |
| **3** | `forecast-worker` (cron, every 5m) | Queries ClickHouse for last 168h of cost data |
| **4** | `forecast-worker` | Runs TimesFM to produce `mean`, `p10`, `p90` for next 24h |
| **5** | `forecast-worker` | Calls `POST /v1/metrics/forecast` on the SDK API with results |
| **6** | `instrumentation-sdk-api` | Sets observable Prometheus gauges: `llm_forecast_cost_mean_usd_micro`, etc. |
| **7** | Prometheus | Scrapes port 9464 every 5s |
| **8** | Grafana | Renders forecast band charts from Prometheus data |

---

## 3. Quick Start (Docker — End User)

### Prerequisites
- Docker Engine 24+ installed
- Ports `8000`, `3000`, `9090`, `4317` available on your host

### Step 1 — Log in to Docker Hub

```bash
docker login -u chiefj
# Enter your token when prompted
```

### Step 2 — Pull both images

```bash
docker pull chiefj/instrumentation-sdk-api:latest
docker pull chiefj/forecast-worker:latest
```

### Step 3 — Start the Observability Stack

Start the main observability stack (FastAPI + Prometheus + Grafana + Tempo in one container):

```bash
docker run -d \
  --name observability-stack \
  -p 8000:8000 \
  -p 3000:3000 \
  -p 9090:9090 \
  -p 4317:4317 \
  chiefj/instrumentation-sdk-api:latest
```

Wait ~10 seconds for all services to start, then verify:

```bash
curl http://localhost:8000/v1/metrics/health
# → {"initialized": true, "message": "# HELP ..."}
```

### Step 4 — Start the Forecast Worker

The worker needs access to your ClickHouse instance and the SDK API:

```bash
docker run -d \
  --name forecast-worker \
  -e CLICKHOUSE_HOST=your-clickhouse-host \
  -e CLICKHOUSE_PORT=8123 \
  -e CLICKHOUSE_DATABASE=llm_observability \
  -e CLICKHOUSE_USER=default \
  -e CLICKHOUSE_PASSWORD=your-password \
  -e INSTRUMENTATION_SDK_URL=http://observability-stack:8000 \
  -e TEMPORAL_HOST=your-temporal-host:7233 \
  --link observability-stack \
  chiefj/forecast-worker:latest
```

> **Tip:** For local development without ClickHouse, you can push forecast results directly to the SDK API (see [Step 5](#step-5--send-forecast-data-from-your-code) below).

### Step 5 — Open Grafana

Navigate to **http://localhost:3000** (default credentials: `admin` / `admin`).

Go to **Dashboards → LLM Observability** folder. You'll see:

| Dashboard | What It Shows |
|-----------|---------------|
| **LLM Cost Forecast Dashboard** | Mean/p10/p90 forecast band, uncertainty width, actual vs forecast overlay |
| **LLM Cost Dashboard** | Cumulative cost, cost by model/service, forecast panel |
| **LLM Security & Safety Dashboard** | PII detections, injection attempts, violation trends |
| **LLM Latency & TTFT Dashboard** | p50/p95/p99 latency, time-to-first-token by model |
| **LLM Guardrails Dashboard** | Invariant breach tracking, human review SLO |

---

## 4. Sending Forecast Data from Your App

If you're integrating your own forecasting model or want to push forecasts programmatically without the Temporal worker, you can call the SDK directly:

### REST API

```bash
curl -X POST http://localhost:8000/v1/metrics/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "mean": 9200,
    "p10": 3800,
    "p90": 17500,
    "model": "gpt-4o",
    "provider": "openai",
    "service_name": "my-chat-app"
  }'
```

| Field | Type | Description |
|-------|------|-------------|
| `mean` | `int` | Expected cost in **micro-USD** (e.g. `9200` = $0.0092) |
| `p10` | `int` | Optimistic lower bound (10th percentile) |
| `p90` | `int` | Pessimistic upper bound (90th percentile) |
| `model` | `str` | LLM model name (e.g. `"gpt-4o"`) |
| `provider` | `str` | LLM provider (e.g. `"openai"`, `"anthropic"`) |
| `service_name` | `str` | Your service identifier |

### Python SDK Usage

```python
import httpx

SDK_URL = "http://localhost:8000"

# Record a span (actual usage)
httpx.post(f"{SDK_URL}/v1/metrics/record", json={
    "model": "gpt-4o",
    "provider": "openai",
    "service_name": "my-chat-app",
    "prompt_tokens": 1500,
    "completion_tokens": 400,
    "latency_ms_total": 1800,
    "latency_ms_ttft": 320,
    "finish_reason": "stop",
    "status": "success",
    "cost_usd_micro": 7200,
    "pii_detected": False,
    "injection_attempt": False,
})

# Push a forecast (from your own model or from forecast-worker output)
httpx.post(f"{SDK_URL}/v1/metrics/forecast", json={
    "mean": 9200,
    "p10": 3800,
    "p90": 17500,
    "model": "gpt-4o",
    "provider": "openai",
    "service_name": "my-chat-app",
})
```

---

## 5. Viewing Forecasts in Grafana

After sending at least one forecast, open Grafana and go to:

**Dashboards → LLM Observability → LLM Cost Forecast Dashboard**

You'll see:

- **Top panel** — Time-series with three lines: `Mean` (blue, solid), `p10` (green, dashed), `p90` (orange, dashed). This is the confidence interval band produced by TimesFM.
- **Bar gauge** — Current forecast mean broken down by model.
- **Uncertainty band width** — How wide the forecast spread is (p90 − p10).
- **Actual vs Forecast** — Actual accumulated cost overlaid with the forecast mean line, so you can validate accuracy.
- **Stat panels** — Current snapshot values for mean, p10, p90.

> **Metric names in Prometheus** (for custom PromQL queries):
> ```
> llm_forecast_cost_mean_usd_micro{model="gpt-4o", service_name="my-chat-app"}
> llm_forecast_cost_p10_usd_micro{model="gpt-4o", service_name="my-chat-app"}
> llm_forecast_cost_p90_usd_micro{model="gpt-4o", service_name="my-chat-app"}
> ```
> Divide by `1000000` to convert from micro-USD to USD.

---

## 6. Core Architectural Pipeline

```
[Cron: 5 * * * *]
       │
       ▼
1. fetch_cost_series (Activity F-FM-01)
       │  Queries ClickHouse cost_by_dimension for last 168 hours
       ▼
2. ForecastService.build_dense_series (Domain Layer)
       │  Zero-pads missing hours, validates min_history_hours >= 48
       ▼
3. TimesFM Inference (Adapter Layer)
       │  google/timesfm-2.5-200m-pytorch
       │  context_len=168, patch_len=32, horizon=24
       ▼
4. Quantile Projection
       ├── forecast_mean → Expected cost trend
       ├── forecast_p10  → Optimistic lower bound
       └── forecast_p90  → Worst-case for budget breach alerting
       │
       ▼
5. POST /v1/metrics/forecast → instrumentation-sdk-api
       │
       ▼
6. OTel Observable Gauge → Prometheus :9464 → Grafana
```

---

## 7. Model Parameters and Caching

- **Checkpoint:** `google/timesfm-2.5-200m-pytorch` (registered in platform Model Registry)
- **Context length:** `168` hours (1 week of history)
- **Input patch length:** `32`
- **Generation horizon:** `24` hours ahead
- **Backend:** PyTorch CPU-only (`torch --index-url https://download.pytorch.org/whl/cpu`)
- **Weight caching:** Mount `~/.cache/huggingface` as a Docker volume to avoid re-downloading on restart:

```bash
docker run -d \
  --name forecast-worker \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  ... \
  chiefj/forecast-worker:latest
```

---

## 8. Database Migrations

Migrations live in `database/migrations/` and use immutable versioned SQL files:

| File | Purpose |
|------|---------|
| `0001_init.sql` | Creates `forecasts` table with `forecast_mean`, `forecast_p10`, `forecast_p90`, `forecast_time`, per service/model (unique constraint) |
| `0001_init.rollback.sql` | Reverts the schema |
| `schema.lock` | Current schema hash lock |

---

## 9. Folder Structure

```
packages/python/forecast-worker/
├── build/
│   └── Dockerfile             # CPU-optimized PyTorch container
├── contracts/
│   └── workflows/
│       └── forecast_workflow.yaml
├── database/
│   ├── migrations/
│   │   ├── 0001_init.rollback.sql
│   │   └── 0001_init.sql
│   └── schema.lock
├── outcome/                   # Generated forecast graphs (PNG/SVG)
├── scripts/
│   └── test.sh
├── src/
│   ├── features/forecast/
│   │   └── service.py         # Dense series + business validation
│   ├── infra/adapters/clickhouse/
│   │   └── clickhouse_adapter.py
│   ├── shared/
│   │   ├── contracts/validator.py
│   │   ├── errors/base.py
│   │   └── ports/clickhouse_port.py
│   └── worker/
│       └── index.py           # Entry point
├── tests/unit/
├── pyproject.toml
├── worker-registry.yaml
└── README.md
```

---

## 10. Development and Testing

### Setup Environment

```bash
python3 -m venv --without-pip .venv
.venv/bin/python3 get-pip.py
.venv/bin/pip install -e ".[dev]"
```

### Run Tests

```bash
./scripts/test.sh
```

Or with coverage:

```bash
.venv/bin/pytest --cov=src --cov-report=term-missing
```

> Minimum coverage threshold: **80%** (currently **94%** package-wide).

---

## 11. Docker Deployment Configurations

We provide Docker files and compose configurations for development, testing, and production.

### Dockerfiles (under `build/`)

- **`Dockerfile.dev`**: Installs packages with dev options (`.[dev]`), mounts code directories, and allows real-time code reloading.
- **`Dockerfile.test`**: A dedicated containerised testing environment pre-installed with all dev dependencies and configured to run `pytest` directly.

### Compose Deployments (under `deploy/docker/`)

- **`docker-compose.dev.yaml`**: Launches PostgreSQL, Redis, ClickHouse, and the forecast-worker in development mode with active volume mounts.
- **`docker-compose.test.yaml`**: Launches PostgreSQL, Redis, ClickHouse, and a test-runner container to execute the test suite in isolation.
- **`docker-compose.prod.yaml`**: Standard configuration designed for production containing the production-built `forecast-worker`.

To run development:
```bash
docker compose -f deploy/docker/docker-compose.dev.yaml up --build
```

To run test suite:
```bash
docker compose -f deploy/docker/docker-compose.test.yaml up --build --abort-on-container-exit
```

---

## 12. REST API Endpoints & SRP Compliance

The HTTP REST API (running on port `8000`) is built with FastAPI. All endpoints comply strictly with the **Single Responsibility Principle (SRP)**. Business logic, mathematical conversions, and query formatting reside in the feature-service layer (`ForecastService`), while database and storage routing reside in `ForecastRepository`—keeping REST handlers thin and focus-bound.

### Endpoints:
1. **`GET /health`** - Basic system check.
2. **`POST /trigger`** - Manual workflow trigger.
3. **`GET /forecasts/cost/{service}/{model}`** - Expected cost forecast.
4. **`GET /forecasts/latency/{service}/{model}`** - Expected latency forecast.
5. **`GET /forecasts/cost/{service}/{model}/breach-risk`** - Checks if predicted cost exceeds budget limit.
6. **`GET /forecasts/summary`** - Full summary of all forecasts and budget status.

---

## Docker Image Reference

| Image | Tag | Size | Description |
|-------|-----|------|-------------|
| `chiefj/instrumentation-sdk-api` | `latest` | ~2.1 GB | FastAPI + Prometheus + Grafana + Tempo all-in-one observability stack |
| `chiefj/forecast-worker` | `latest` | ~3.5 GB | TimesFM CPU inference worker + Temporal integration |
| `chiefj/forecast-worker` | `dev` | — | Dev-enabled image including dev dependencies and source mounts |
| `chiefj/forecast-worker` | `test` | — | Isolated test-runner image with pytest installed |

