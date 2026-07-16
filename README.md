# LLM Observability Platform: Core Python Infrastructure

This guide covers the technical architecture and end-user usage for the Python-based observability components.

## Table of Contents
- [🆕 What's New (v1.13.0)](#-whats-new-v1130)
- [1. System Architecture](#1-system-architecture)
  - [High-Level Data Flow](#high-level-data-flow)
  - [Technical Sequence](#technical-sequence)
- [2. End-User Usage Guide](#2-end-user-usage-guide)
  - [Installation](#installation)
  - [Auto-Instrumentation (Zero-Code Changes)](#auto-instrumentation-zero-code-changes)
  - [Remote Management API (REST)](#remote-management-api-rest)
  - [Basic Usage: Decorators](#basic-usage-decorators)
  - [Advanced Usage: Context Manager](#advanced-usage-context-manager)
  - [Token Counting (Pre-Call Token Counting)](#token-counting-pre-call-token-counting)
  - [Streaming Observability (TTFT & Token Tracking)](#streaming-observability-ttft--token-tracking)
  - [PII & Injection Scan (Aho-Corasick Redaction)](#pii--injection-scan-aho-corasick-redaction)
  - [Deterministic Sampling Gate (Modulo 100)](#deterministic-sampling-gate-modulo-100)
  - [MiniLM Embedding (Concurrent & Sampled)](#minilm-embedding-concurrent--sampled)
  - [Prometheus Metrics & Grafana Dashboards](#prometheus-metrics--grafana-dashboards)
  - [Updating Config Files (Model Prices, PII Patterns, Infra)](#updating-config-files-model-prices-pii-patterns-infra)
  - [Docker Deployment](#docker-deployment)
  - [Observability Launcher CLI (llm-observe)](#observability-launcher-cli-llm-observe)
  - [Temporal EWMA Worker & Cost Anomaly Detection (Standalone)](#temporal-ewma-worker--cost-anomaly-detection-standalone)
- [3. Implementation Call Chain](#3-implementation-call-chain)

---

## 🆕 What's New (v1.13.0)

### Two New Docker Images — Grafana Forecast Observability

This release ships two updated images and a completely new forecast intelligence pipeline:

| Image | Docker Hub | What's Inside |
|-------|-----------|---------------|
| `chiefj/instrumentation-sdk-api:latest` | [→ Hub](https://hub.docker.com/r/chiefj/instrumentation-sdk-api) | FastAPI + **Prometheus + Grafana + Tempo** all-in-one. Now includes 11 auto-provisioned dashboards and the `/v1/metrics/forecast` endpoint. |
| `chiefj/forecast-worker:latest` | [→ Hub](https://hub.docker.com/r/chiefj/forecast-worker) | New — **Google TimesFM 2.5-200m** cron worker. Runs every 5 minutes, forecasts LLM costs 24 hours ahead (mean / p10 / p90), pushes results to the SDK API. |

```bash
docker pull chiefj/instrumentation-sdk-api:latest
docker pull chiefj/forecast-worker:latest
```

### What Changed

- **`PrometheusMetricsAdapter`** — switched forecast gauges from push-based (`create_gauge`) to **observable callback-based** (`create_observable_gauge`). Forecast values now persist on every Prometheus scrape cycle instead of expiring after one collection.
- **`POST /v1/metrics/forecast`** — new REST endpoint to push `mean / p10 / p90` forecast values (in micro-USD) directly from any source.
- **11 Grafana dashboards** — all auto-provisioned in the `LLM Observability` folder. Queries now use correct OTel Prometheus metric name conventions (`_usd_micro` suffix on gauges).
- **`forecast-worker` package** — new Temporal-based cron worker using Google TimesFM for proactive cost forecasting (see [`packages/python/forecast-worker/README.md`](packages/python/forecast-worker/README.md)).

### How the Two Images Connect

```
┌──────────────────────────┐     POST /v1/metrics/forecast     ┌──────────────────────────────┐
│  chiefj/forecast-worker  │ ──────────────────────────────►  │ chiefj/instrumentation-sdk-api│
│                          │                                   │                              │
│  TimesFM inference every │                                   │  OTel Observable Gauge       │
│  5 minutes on ClickHouse │                                   │  → Prometheus :9464          │
│  168h cost history       │                                   │  → Grafana dashboards        │
└──────────────────────────┘                                   └──────────────────────────────┘
```

### Grafana Dashboards — What You Can See

Open Grafana at **http://localhost:3000** → **Dashboards → LLM Observability**

| Dashboard | Panels | Key Metrics Shown |
|-----------|--------|-------------------|
| **LLM Cost Forecast** ⭐ | 7 | Mean/p10/p90 confidence band, uncertainty width (p90−p10), actual vs forecast overlay, per-model bar gauge, stat snapshots |
| **LLM Cost** | 4 | Cumulative cost over time, cost by model (donut), cost by service (bar gauge), forecast panel |
| **LLM Latency & TTFT** | 6 | p50/p95/p99 total latency, p50/p95/p99 time-to-first-token, avg latency by model |
| **LLM Security & Safety** | 8 | PII detection rate, injection attempt rate, total violations stat, violations over time, breakdown by service & model |
| **LLM Guardrails** | 4 | Invariant breach tracking (INV-Q-01 to INV-Q-07), human review SLO %, review decisions pie chart |
| **LLM Error & Retry** | 4 | Error rate by status, retry distribution, finish reason breakdown, retry count trend |
| **LLM Model Parity & A/B** | 3 | Cost per request by model, token efficiency ratio, latency parity comparison |
| **LLM Quality Engine** | 3 | Quality score distribution, evaluation throughput, score trend over time |
| **LLM Data Drift** | 3 | Token distribution drift, cost baseline deviation, latency drift |
| **LLM System Performance** | 3 | HTTP server active requests, request duration P95, memory/CPU usage |
| **LLM User Analytics** | 3 | Spans per service, unique model usage, request volume trend |

### Prometheus Metrics Reference (all live)

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `llm_tokens_total` | Counter | `model, provider, service_name, token_type` | Total tokens consumed (prompt / completion) |
| `llm_cost_usd_micro_total` | Counter | `model, provider, service_name` | Accumulated cost in micro-USD |
| `llm_latency_ms_total` | Histogram | `model, provider, service_name` | End-to-end call latency (ms) |
| `llm_latency_ms_ttft` | Histogram | `model, provider, service_name` | Time to first token (ms) |
| `llm_finish_reason_total` | Counter | `model, provider, service_name, finish_reason` | Finish reason distribution |
| `llm_spans_total` | Counter | `model, provider, service_name, status` | Total LLM spans recorded |
| `llm_pii_detected_total` | Counter | `model, provider, service_name` | PII detections count |
| `llm_injection_attempts_total` | Counter | `model, provider, service_name` | Prompt injection attempts count |
| `llm_forecast_cost_mean_usd_micro` | Gauge | `model, provider, service_name` | TimesFM forecast mean cost (micro-USD) |
| `llm_forecast_cost_p10_usd_micro` | Gauge | `model, provider, service_name` | Forecast p10 optimistic bound |
| `llm_forecast_cost_p90_usd_micro` | Gauge | `model, provider, service_name` | Forecast p90 pessimistic bound |

> Convert micro-USD to USD: divide by `1,000,000`  
> Example PromQL: `sum(llm_forecast_cost_mean_usd_micro) by (model) / 1000000`

### Quick Start — Both Images Together

```bash
# 1. Start the observability stack (API + Prometheus + Grafana + Tempo)
docker run -d \
  --name observability-stack \
  -p 8000:8000 \
  -p 3000:3000 \
  -p 9090:9090 \
  -p 4317:4317 \
  chiefj/instrumentation-sdk-api:latest

# 2. Start the forecast worker (connects to observability-stack)
docker run -d \
  --name forecast-worker \
  -e CLICKHOUSE_HOST=your-clickhouse-host \
  -e CLICKHOUSE_PASSWORD=your-password \
  -e INSTRUMENTATION_SDK_URL=http://observability-stack:8000 \
  -e TEMPORAL_HOST=your-temporal:7233 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --link observability-stack \
  chiefj/forecast-worker:latest

# 3. Push a forecast manually (no worker needed for testing)
curl -X POST http://localhost:8000/v1/metrics/forecast \
  -H "Content-Type: application/json" \
  -d '{"mean": 9200, "p10": 3800, "p90": 17500, "model": "gpt-4o", "provider": "openai", "service_name": "my-app"}'

# 4. Open Grafana → http://localhost:3000 → Dashboards → LLM Observability
```

---

## 1. System Architecture

### High-Level Data Flow
This diagram illustrates the lifecycle of a span from application capture to background enrichment. The SDK now includes a REST Management API for remote control and discovery.

```text
┌────────────────┐          ┌──────────────────┐          ┌───────────────────┐
│   User App     │ capture  │ instrumentation  │  queue   │  Cloudflare Queue │
│  (Python/JS)   ├─────────>│      -sdk        ├─────────>│ (span-enrichment) │
└────────────────┘          └─────────┬────────┘          └─────────┬─────────┘
                                      │                             │
                                      │ REST API (8000)             │ trigger
                                      v                             v
┌────────────────┐          ┌──────────────────┐          ┌───────────────────┐
│ Analytics DB   │ storage  │  Remote Control  │ response │  queue-embedding  │
│ (ClickHouse)   │<─────────┤  (Init/Detect)   │<─────────┤      -worker      │
└────────────────┘          └──────────────────┘          └─────────┬─────────┘
                                                                    │
                                                                    │ HTTP call
                                                                    v
                                                          ┌───────────────────┐
                                                          │ Cloudflare AI     │
                                                          │ (Workers AI API)  │
                                                          └───────────────────┘
```


## 2. End-User Usage Guide

The `instrumentation-sdk` is designed to be developer-friendly, requiring minimal code changes to start capturing observability data.

### Installation
```bash
pip install instrumentation-sdk
```

### Auto-Instrumentation (Zero-Code Changes)
The fastest way to get observability is to use auto-instrumentation. This patches the underlying HTTP calls of popular LLM clients transparently.

```python
from instrumentation_sdk import init_auto_instrumentation

# Initialize at the start of your application
init_auto_instrumentation()

# Now any call to OpenAI, Anthropic, LiteLLM, or LangChain is tracked automatically
import openai
client = openai.AsyncOpenAI()
response = await client.chat.completions.create(model="gpt-4o", messages=[...])
```

**Supported Providers:**
- **OpenAI**: `openai.AsyncOpenAI`
- **Anthropic**: `anthropic.AsyncAnthropic`
- **LiteLLM**: `litellm.acompletion`
- **LangChain**: Any model inheriting from `BaseChatModel` (via `ainvoke`)

### Remote Management API (REST)
The SDK provides a built-in FastAPI-based management layer for remote orchestration.

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/instrumentation/init` | POST | Remotely initialize auto-instrumentation. |
| `/instrumentation/uninstrument` | POST | Disable all active instrumentation. |
| `/instrumentation/detect` | POST | Discovery: Detect provider/model from a sample request body. |
| `/instrumentation/test-call` | POST | Verification: Trigger a sample LLM call to verify end-to-end tracing. |
| `/streaming/test-stream-call` | POST | Verification: Trigger a mock streaming call to verify streaming/TTFT. |
| `/v1/sampling/should-sample` | POST | Verification: Check if a span should be sampled. |
| `/v1/embeddings/embed` | POST | Verification: Generate MiniLM embeddings for a given text. |
| `/v1/spans` | POST | Ingestion: Submit a span to the reliable reporter for storage & delivery. |
| `/v1/fallback/track` | POST | Ingestion: Track model fallback retry attempts for a trace ID. |
| `/v1/fallback/clear` | POST | Clean up: Clear the fallback tracker memory. |
| `/v1/tool-call/track` | POST | Ingestion: Track span cost and get trace cumulative cost. |
| `/v1/tool-call/clear` | POST | Clean up: Clear the tool-call tracker memory. |
| `/v1/metrics/prices` | GET | Retrieval: Get the list of all current model prices. |
| `/v1/metrics/prices/reload` | POST | Management: Manually trigger a reload of model prices. |

### Basic Usage: Decorators
Use the `@llm_observe` decorator to manually track functions.

```python
from instrumentation_sdk import llm_observe

# (1) Decorate your LLM-calling functions
@llm_observe(service="payment-bot", endpoint="gpt-4o")
def get_llm_response(prompt: str):
    # Your existing LLM logic here
    # status, latency, and span_ids are captured automatically
    return response

# (2) Support for Async functions
@llm_observe(service="search-agent", endpoint="claude-3")
async def get_async_response(prompt: str):
    return await client.completions.create(...)
```

### Advanced Usage: Context Manager
For callers who need to set metadata mid-call (e.g., after routing to a specific model or determining usage), use the `llm_span` context manager. It supports both synchronous and asynchronous usage.

```python
from instrumentation_sdk import llm_span

async def my_handler(req):
    # (1) Start a span with initial metadata
    async with llm_span(model="gpt-4o", user_id=req.user_id) as span:
        # (2) Perform your LLM call
        response = await client.chat.completions.create(...)
        
        # (3) Update metadata mid-call
        span.set_metadata("actual_model", response.model)
        span.set_metadata("prompt_tokens", response.usage.prompt_tokens)
        
    # Span is automatically reported on exit (even if an error occurs)
```

### Manual Reporting
If you prefer direct control over the span data, you can use the reporter manually.

```python
from instrumentation_sdk import get_reporter

reporter = get_reporter()
reporter.report({
    "span_id": "unique-id",
    "service_name": "my-service",
    "status": "success",
    "text": "The prompt content to be enriched"
})
```

### Docker Deployment
The instrumentation SDK API is available as a production-ready, fully self-contained **All-in-One Standalone Observability Container**. This container bundles the FastAPI application, Grafana, and Tempo into a single image, eliminating the need to set up external databases or visualizers manually.

**Image Name:** `chiefj/instrumentation-sdk-api:unstable` (or `chiefj/instrumentation-sdk-api:latest`)

To pull and run the fully integrated all-in-one container locally:
```bash
# Pull the latest standalone image
docker pull chiefj/instrumentation-sdk-api:unstable

# Run the unified all-in-one telemetry stack
docker run -d \
  -p 8002:8000 \
  -p 3002:3000 \
  --name instrumentation-api-allinone \
  chiefj/instrumentation-sdk-api:unstable
```

* **API Endpoints**: Accessible at `http://localhost:8002`
* **Grafana Portal**: Accessible at `http://localhost:3002` (Tempo is automatically provisioned as a read-only datasource and ready to query!)

### Observability Launcher CLI (`llm-observe`)

To simplify launching and managing the all-in-one container, the SDK provides a built-in command-line utility named `llm-observe`.

Once `instrumentation-sdk` is installed, you can manage the observability stack with simple commands:

```bash
# Start the stack on host ports: API (8002), Grafana (3002), OTLP (4317), Prometheus (9090)
llm-observe start

# Check the status of the container stack
llm-observe status

# Stop and clean up the container stack
llm-observe stop
```

#### Customizing Ports & Names
You can customize the container name, ports, image, and tag:
```bash
llm-observe start --name my-observability --api-port 8005 --grafana-port 3005
```

For development with hot-reloading, use the provided Docker Compose:
```bash
docker compose -f packages/python/instrumentation-sdk/deploy/docker/docker-compose.dev.yaml up instrumentation-api
```

### Token Counting (Pre-Call Token Counting)

The SDK provides automatic pre-call token counting utilizing `tiktoken` with fallback character-based heuristics for non-OpenAI models. It supports plain text strings, complex chat message list schemas, and OpenAI's tile-based vision token calculation.

#### Direct Token Counting

Use `count_tokens` to calculate tokens directly:

```python
from instrumentation_sdk import count_tokens

tokens, method = count_tokens("hello world", "gpt-4")
```

#### Context Manager with Automated Token Tracking

Use `llm_span_with_tokens` to automatically record `prompt_tokens` and `token_count_method` inside manual spans:

```python
from instrumentation_sdk import llm_span_with_tokens

async def handle_request(req):
    async with llm_span_with_tokens(model="gpt-4", provider="openai", prompt="hello world") as span:
        pass
```

#### REST Management API (REST)

The `/v1/token-counting/count` REST API endpoint supports counting prompt tokens:

```bash
curl -X POST http://localhost:8000/v1/token-counting/count \
  -H "Content-Type: application/json" \
  -d '{"prompt": "hello world", "model": "gpt-4"}'
```

### Streaming Observability (TTFT & Token Tracking)

The SDK provides specialized utilities for tracking streaming LLM calls. It wraps generators/iterators to:
- Capture the **Time-to-First-Token (TTFT)** latency when the first chunk is yielded.
- Accumulate the streamed chunks and automatically compute the completion token count (using Tiktoken/heuristics) upon stream completion or cancellation.
- Finalize and report the manual span only when the stream is exhausted, closed, or encounters an exception.

#### Basic Streaming Usage

Use `llm_streaming_span`, `wrap_stream` (for synchronous generators), and `wrap_async_stream` (for asynchronous generators):

```python
from instrumentation_sdk import llm_streaming_span, wrap_stream, wrap_async_stream

# 1. Synchronous Streaming
with llm_streaming_span(model="gpt-4", provider="openai", prompt="Say hello") as span_ctx:
    raw_generator = ["Hello", " world", "!"]
    wrapped_stream = wrap_stream(raw_generator, span_context=span_ctx, model="gpt-4")
    for chunk in wrapped_stream:
        print(chunk)

# 2. Asynchronous Streaming
async with llm_streaming_span(model="gpt-4", provider="openai", prompt="Say hello") as span_ctx:
    async def async_generator():
        yield "Hello"
        yield " world"
    wrapped_stream = wrap_async_stream(async_generator(), span_context=span_ctx, model="gpt-4")
    async for chunk in wrapped_stream:
        print(chunk)
```

#### Mid-Stream Updates & Abort Resilience
- You can dynamically update span metadata using `span_ctx.set_metadata("custom_field", "value")` mid-stream.
- If the stream is closed early (via `wrapped_stream.close()` or `.aclose()`), the SDK captures and reports all completion tokens generated up to that point.

#### REST Verification Endpoint

The `/v1/streaming/test-stream-call` endpoint streams SSE events back to the client while validating end-to-end streaming tracing:

```bash
curl -X POST http://localhost:8000/v1/streaming/test-stream-call \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "chunks": ["A", "B", "C"]}'
```

### PII & Injection Scan (Aho-Corasick Redaction)

The SDK features an inline Aho-Corasick trie-based scanner that runs on all prompts inside manual span contexts (`LLMSpanContext` and `LLMSpanWithTokensContext`). It intercepts prompts, detects PII and SQL/prompt injection, and updates telemetry accordingly.

#### Redaction & Interception Behavior
- **PII Detected**: The prompt and downstream fields (like hashes and embeddings) are completely redacted (`None` or empty). The custom span attribute `llm.pii_detected` is set to `True`.
- **Injection Detected**: The prompt is preserved, but the custom span attribute `llm.injection_attempt` is set to `True`.
- **Fail-Safe execution**: Any exception raised inside the scanning engine is caught internally, allowing client code or FastAPI handler to execute without crashes.

#### Programmatic Scan Usage
You can import and call `scan_prompt` directly to inspect a prompt:

```python
from instrumentation_sdk import scan_prompt

# Returns (pii_detected: bool, injection_attempt: bool)
pii, inj = scan_prompt("my email is test@example.com")
print(f"PII: {pii}, Injection: {inj}")
```

#### REST Scanning Endpoint
The `/v1/pii-injection/scan` REST API endpoint supports checking prompt contents:

```bash
curl -X POST http://localhost:8000/v1/pii-injection/scan \
  -H "Content-Type: application/json" \
  -d '{"prompt": "my email is user@example.com"}'
```

### Deterministic Sampling Gate (Modulo 100)

The SDK implements deterministic sampling decided at span creation time. It hashes the `span_id` using SHA256 and evaluates whether the hash value modulo 100 is equal to 0.
- Sampled (`is_sampled` is `True`): The span is processed normally, performing prompt hashing and embedding generation.
- Unsampled (`is_sampled` is `False`): The span drops/skips both the SHA256 hashing and the MiniLM embedding generation, saving computational resources.

#### Programmatic Usage
You can query the sampling logic directly:
```python
from instrumentation_sdk import should_sample

sampled = should_sample("test-span-id")
```

#### REST Endpoint
Query the `/v1/sampling/should-sample` endpoint to check sampling:
```bash
curl -X POST http://localhost:8000/v1/sampling/should-sample \
  -H "Content-Type: application/json" \
  -d '{"span_id": "test-span-id"}'
```

### MiniLM Embedding (Concurrent & Sampled)

The SDK asynchronously calls the embedding-worker HTTP endpoint (`POST /embed`) to generate a 384-dimensional vector embedding of the prompt text.

- **Concurrent Execution**: To prevent blocking client requests, the SDK uses `asyncio.create_task()` to fire the embedding generation concurrently with span finalization.
- **Conditionality**: The embedding is only generated if the span is sampled (`is_sampled` is `True`) and no PII is detected in the prompt (`pii_detected` is `False`).
- **Timeout and Resilience**: The embedding HTTP request has a timeout of 500ms. If the request times out or fails, the SDK falls back to `None` for the embedding field while the rest of the span details are still successfully emitted.

#### Programmatic Usage
```python
from instrumentation_sdk import get_embedding

embedding = await get_embedding("your text here")
```

#### REST Endpoint
```bash
curl -X POST http://localhost:8000/v1/embeddings/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "your text here"}'
```

### Prometheus Metrics & Grafana Dashboards

The SDK integrates a full Prometheus + Grafana pipeline. **11 dashboards** are auto-provisioned in the `LLM Observability` folder when you run the container.

#### Metrics API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/metrics/init` | POST | Initialize Prometheus scraping on port 9464 |
| `/v1/metrics/health` | GET | Health check + raw Prometheus output |
| `/v1/metrics/record` | POST | Record a single LLM span (tokens, cost, latency) |
| `/v1/metrics/record-batch` | POST | Record multiple spans in one call |
| `/v1/metrics/forecast` | POST | Push TimesFM forecast values (mean/p10/p90) |
| `/v1/metrics/prices` | GET | Get current model prices |
| `/v1/metrics/prices/reload` | POST | Hot-reload model prices |

#### Record a Span

```bash
curl -X POST http://localhost:8000/v1/metrics/record \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "provider": "openai",
    "service_name": "my-app",
    "prompt_tokens": 1500,
    "completion_tokens": 400,
    "latency_ms_total": 1800,
    "latency_ms_ttft": 320,
    "finish_reason": "stop",
    "status": "success",
    "cost_usd_micro": 7200,
    "pii_detected": false,
    "injection_attempt": false
  }'
```

#### Push a Forecast

```bash
curl -X POST http://localhost:8000/v1/metrics/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "mean": 9200,
    "p10": 3800,
    "p90": 17500,
    "model": "gpt-4o",
    "provider": "openai",
    "service_name": "my-app"
  }'
```

#### Grafana Dashboards (11 total)

Open **http://localhost:3000** → **Dashboards → LLM Observability**:

| Dashboard | What You'll See |
|-----------|----------------|
| ⭐ **LLM Cost Forecast** | Mean/p10/p90 confidence band, uncertainty width, actual vs forecast overlay |
| **LLM Cost** | Cumulative cost over time, cost by model & service |
| **LLM Latency & TTFT** | p50/p95/p99 latency and time-to-first-token by model |
| **LLM Security & Safety** | PII detection rate, injection attempts, violations by service |
| **LLM Guardrails** | Invariant breach tracking, human review SLO % |
| **LLM Error & Retry** | Error rates, finish reasons, retry distribution |
| **LLM Model Parity & A/B** | Cost per request, token efficiency, latency comparison |
| **LLM Quality Engine** | Quality score distribution and evaluation throughput |
| **LLM Data Drift** | Token distribution and cost baseline deviation |
| **LLM System Performance** | HTTP server metrics, CPU/memory usage |
| **LLM User Analytics** | Spans per service, request volume trend |

### Updating Config Files (Model Prices, PII Patterns, Infra)

The SDK reads config files once at startup. For PII patterns and infra configs, a container restart is required. Model prices (`model_prices.yaml`) and Grafana dashboard JSON files are hot-reloaded automatically.

#### Adding or updating a model price

Edit `config/model_prices.yaml`:

```yaml
- model: gpt-5
  provider: openai
  input_price_per_1m: 10.00
  output_price_per_1m: 30.00
  version: "2026-01-01"
```

Required fields: `model`, `provider`, `input_price_per_1m`, `output_price_per_1m`, `version`.  
Prices must be `>= 0`. Duplicate `(model, provider)` pairs are rejected by CI.

The model prices are watched and hot-reloaded automatically when the configuration file changes. You can also manually trigger a reload via the API:
```bash
curl -X POST http://localhost:8000/v1/metrics/prices/reload
```


#### Adding or updating a PII / Injection pattern

Edit `config/patterns.yaml`:

```yaml
patterns:
  - name: phone_number
    regex: "\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b"
    type: PII_STRUCTURAL   # or INJECTION_ATTEMPT
```

Valid `type` values: `PII_STRUCTURAL`, `INJECTION_ATTEMPT`.  
The CI validates that every regex compiles and no pattern name is duplicated.

Then restart:
```bash
docker restart instrumentation-sdk-api
```

#### Updating a Grafana dashboard

Edit any file under `build/dashboards/*.json`.  
**No restart required** — Grafana polls and hot-reloads dashboards every 30 seconds automatically.

#### Updating infra configs (Grafana datasource, Prometheus, Tempo)

Edit:
- `build/grafana-datasource.yaml` — add/change datasources
- `build/grafana-dashboard-provider.yaml` — change dashboard provider path/folder
- `build/prometheus.yml` — add scrape targets
- `build/tempo-config.yaml` — change Tempo storage or OTLP port

#### Running the Automated Performance Report Generator

To benchmark the Reliable Kafka Reporter (evaluating in-memory queueing, offline SQLite WAL fallback writing, and recovery replay throughput) and automatically compile the premium HTML dashboard report, run the performance test suite:

```bash
cd packages/python/instrumentation-sdk
PYTHONPATH=. .venv/bin/pytest tests/performance/
```

This dynamically compiles and generates `reports/performance-report.html` with a modern dark-mode interface and interactive Chart.js visualization.

#### Production Deployment Modes

Two Docker Compose configurations are available under `deploy/docker/` depending on your setup:

1. **All-in-One Mode (Zero Setup)**: Starts the FastAPI API, Kafka, Zookeeper, pgvector Postgres, Clickhouse, and Redis fully integrated and pre-configured out of the box:
   ```bash
   docker compose -f deploy/docker/docker-compose.prod-all.yaml up -d
   ```

2. **Standalone Mode (Plug-and-Play)**: Starts only the API container, allowing you to connect to your own existing Kafka cluster and databases by supplying environment variables:
   ```bash
   KAFKA_BOOTSTRAP_SERVERS="my-kafka:9092" docker compose -f deploy/docker/docker-compose.prod.yaml up -d
   ```

#### Multi-Environment Deployment Suite (All 13 Services)

For deploying the entire LLM Observability Platform stack (including ZooKeeper, Kafka, pgvector Postgres, Clickhouse, Redis, Temporal, and all 7 worker/scorer microservices), we provide a unified deployment package:

* **Location**: [`packages/configs/observability-deploy/`](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/observability-deploy/)
* **Configuration Formats**: Docker Compose, Kubernetes manifests, cloud Terraform setups (AWS, GCP, Azure), and Ansible playbooks.
* **Launch Command**:
  ```bash
  ./packages/configs/observability-deploy/scripts/deploy.sh
  ```

##### Hardware Resource Requirements

Running the full suite of 13 services concurrently requires a baseline level of system resources due to the integration of stateful databases (ClickHouse, Postgres, Redis), Kafka, Temporal, and model inference workers (Google TimesFM).

1. **Local Development (Docker Compose)**:
   - **RAM**: 12 GB memory minimum allocated to Docker (16 GB recommended).
   - **CPU**: 4 vCPUs minimum (6 vCPUs recommended).
   - **Storage**: 30 GB free disk space (SSD recommended).

2. **Production / Cloud Deployments (EKS/GKE/AKS & Terraform)**:
   - **Kubernetes Nodes**: Minimum of 3 worker nodes (AWS: `t3.large`/`t3.xlarge`, GCP: `e2-standard-4`, Azure: `Standard_D4s_v5`).
   - **Cloud-Managed Databases**: PostgreSQL (`db.t3.medium` on AWS / Flexible Server on Azure), Redis (`cache.t3.medium` on AWS / Azure Cache on Azure), and AWS MSK / GCP Managed Kafka.

### Docker Deployments (v1.13.0)

We publish official Docker images to the `chiefj` namespace on Docker Hub:

| Image | Tag | Description |
|-------|-----|-------------|
| [`chiefj/instrumentation-sdk-api`](https://hub.docker.com/r/chiefj/instrumentation-sdk-api) | `latest` | **All-in-One Observability Stack** — FastAPI + Prometheus + Grafana + Tempo + 11 dashboards auto-provisioned |
| [`chiefj/forecast-worker`](https://hub.docker.com/r/chiefj/forecast-worker) | `latest` | **🆕 TimesFM Forecast Worker** — Google TimesFM 2.5-200m cron worker, pushes mean/p10/p90 forecast to SDK API |
| `chiefj/instrumentation-sdk-api-nokafka` | `stable` | Lightweight standalone without embedded databases |
| `chiefj/toxicity-worker` | `stable` | ONNX toxicity scorer microservice |
| `chiefj/quality-engine` | `stable` | Span quality evaluation + Temporal orchestrator |
| `chiefj/alert-engine` | `stable` | Kafka consumer alert dispatcher (Slack / PagerDuty) |

Each engine contains a `deploy_docker.sh` utility under its `scripts/` directory to build, validate, push, and automatically clean up the local image caches.

#### Architectural Connection Flow

The following diagram illustrates how the three standalone services interact:

```text
┌───────────────────────┐
│  instrumentation-sdk  │──(Publish Spans)──> [ Kafka: llm.spans.sampled ]
└───────────────────────┘                                │
                                                         v
┌───────────────────────┐                    ┌───────────────────────┐
│    Toxicity Worker    │<──(POST /score)────│    Quality Engine     │
│  (chiefj/toxic-bert)  │                    │ (Temporal Orchestrator)│
└───────────────────────┘                    └───────────┬───────────┘
                                                         │
                                                  (Emit Alerts)
                                                         │
                                                         v
┌───────────────────────┐                    [ Kafka: alert topics ]
│     Alert Engine      │<──(Consume Alerts)─────────────┘
│ (Slack / PagerDuty)   │
└───────────────────────┘
```

1. **Telemetry Ingestion**: The `instrumentation-sdk` streams intercepted LLM spans into the `llm.spans.sampled` Kafka topic.
2. **Quality Orchestration**: The **Quality Engine** consumes these spans and triggers a Temporal workflow, which queries the **Toxicity Worker** (via HTTP POST `/score`) and other scorer microservices to evaluate the content.
3. **Alert Routing**: High-toxicity flags and quality degradation events are emitted to Kafka alert topics. The **Alert Engine** consumes these events and dispatches notifications to PostgreSQL databases, Slack channels, and PagerDuty endpoints.

#### How to Run & Use the Microservices

* **Toxicity Scorer Worker** (FastAPI Scorer API):
  Run container on port `8008`:
  ```bash
  docker run -d -p 8008:8008 --name toxicity-worker chiefj/toxicity-worker:stable
  ```
  Score text via HTTP POST request:
  ```bash
  curl -X POST http://localhost:8008/score -H "Content-Type: application/json" -d '{"text": "Is this text toxic?"}'
  ```

* **Quality Scorer Engine** (Kafka Ingestion + Temporal Orchestrator):
  Run container:
  ```bash
  docker run -d --name quality-engine -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 -e POSTGRES_HOST=postgres -e TEMPORAL_HOST=temporal:7233 chiefj/quality-engine:stable
  ```

* **Alert Engine** (Kafka Consumer Alert Dispatcher):
  Run container:
  ```bash
  docker run -d --name alert-engine -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 -e POSTGRES_URL=postgresql://user:pass@postgres:5432/db chiefj/alert-engine:stable
  ```




#### Connection & Configuration Environment Variables

| Environment Variable | Description | Default (All-in-One) | Default (Standalone) |
| :--- | :--- | :--- | :--- |
| `WITH_KAFKA` | Enable embedded Kafka & Postgres server inside container | `true` | `false` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers connection string | `localhost:9092` | (None) |
| `POSTGRES_URL` | PostgreSQL connection string | `postgresql://admin:password@localhost:5432/llm_observability` | (None) |
| `DEPLOYMENT_ENV` | SDK deployment environment (`production`, `staging`, `dev`) | `production` | `production` |

#### Architectural Integration Flow

```
                  [ SDK Telemetry Ingestion Decision Tree ]

                         [ Initiate LLM API Call ]
                                     │
                                     ▼
                          [ Capture Metrics/Span ]
                                     │
                                     ▼
                          [ Check REST API Status ]
                                   /   \
                                 Online Offline
                                 /       \
                                ▼         ▼
                     [ Send to REST API ] [ Write to SQLite WAL ]
                      (POST /v1/spans)    (/tmp/llm-obs-wal.db)
                             │                    │
                             ▼                    ▼
                    [ API Server Side ]    [ Retrying Connection ]
                             │                    │
                   [ Check DB/Kafka Config ]      │
                             │                    │
                     ┌───────┴───────┐            │
                  Enabled         Disabled        │
                     │               │            │
                     ▼               ▼            │
             [ Write to Kafka ] [ Log / NoOp ]    │
          (llm.spans.raw topic)  (Prometheus/     │
                     │            Tempo local)    │
                     ▼                            │
              [ Consumer reads ]                  │
              [  from Kafka    ]                  │
                     │                            │
                     ▼                            │
             [ Write to Postgres ]                │
            (llm_spans partitioned)               │
                     │                            │
                     └────────────────────┬───────┘
                                          │
                                          ▼
                               [ Spans Visualized ]
                             (Grafana http://3000)
```

#### Ingestion Sequence Flow

```
                        [ SDK Telemetry Sequence Flow ]

User App             SDK Client          REST Ingestion       Kafka Broker        PostgreSQL
   │                      │                    │                   │                  │
   │─── LLM Call ────────>│                    │                   │                  │
   │                      │─── Format Span ───>│                   │                  │
   │                      │                    │                   │                  │
   │                      │─── POST /spans ───>│                   │                  │
   │                      │    (HTTP 200 OK)   │                   │                  │
   │                      │                    │─── Produce span ─>│                  │
   │                      │                    │    to topic       │                  │
   │                      │                    │                   │─── Consume ─────>│
   │                      │                    │                   │    & Partition   │
   │                      │                    │                   │    to DB         │
   │                      │                    │                   │                  │
   │ [If API Offline]     │                    │                   │                  │
   │                      │─── Write to WAL ──>│                   │                  │
   │                      │    (SQLite local)  │                   │                  │
   │                      │                    │                   │                  │
   │ [When API Restored]  │                    │                   │                  │
   │                      │─── Replay Spans ──>│                   │                  │
   │                      │    to REST API     │                   │                  │
```

#### Running the load test locally

```bash
cd packages/python/instrumentation-sdk
.venv/bin/python -m pytest tests/performance/ -m performance -v
```

This sends spans covering all 6 model/provider combos, error ratios, PII flags, and high token counts.

### Temporal EWMA Worker & Cost Anomaly Detection (Standalone)

The `temporal-ewma-worker` is a decoupled microservice designed to periodically compute Exponentially Weighted Moving Average (EWMA) baselines for LLM usage costs and detect anomalous cost spikes. 

It runs a FastAPI management server alongside a Temporal worker within a single container.

#### Redis Baseline Cache Path
The calculated baselines are pushed to Redis cache for instant, sub-millisecond retrieval by the ingestion pipeline:
* **Key Format**: `ewma:cost:{service}:{model}:{hour_of_week}`
* **Hour of Week (`hour_of_week`)**: An integer from `0` to `167` representing the hour starting from Monday 00:00 (0) to Sunday 23:00 (167).

#### Standalone Setup & Execution

An end-user can install and run this package individually by following these steps:

1. **Install the package and dependencies**:
   ```bash
   pip install -e packages/python/temporal-ewma-worker
   ```

2. **Spin up local infrastructure**:
   This runs ClickHouse, PostgreSQL, Redis, Kafka, and Temporal:
   ```bash
   docker compose -f packages/python/temporal-ewma-worker/deploy/docker/docker-compose.yaml up -d
   ```

3. **Configure the environment**:
   ```bash
   cp packages/python/temporal-ewma-worker/.env.example packages/python/temporal-ewma-worker/.env
   ```

4. **Apply database migrations**:
   Apply SQL migration schemas to PostgreSQL:
   ```bash
   ./packages/python/temporal-ewma-worker/scripts/migrate.sh up
   ```

5. **Run test verification**:
   Verify configuration and end-to-end integration flows:
   ```bash
   ./packages/python/temporal-ewma-worker/scripts/test.sh
   ```

6. **Start the Worker & FastAPI Server**:
   Start both services concurrently inside a single process:
   ```bash
   ./packages/python/temporal-ewma-worker/scripts/run.sh
   ```

#### REST Management API

The worker exposes a REST management layer on port `8000`:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | GET | Retrieve worker configuration and running environment status |
| `/trigger` | POST | Trigger the EWMA baseline calculation workflow on-demand |

##### Trigger Baseline Calculation On-Demand:
```bash
curl -X POST http://localhost:8000/trigger \
  -H "Content-Type: application/json" \
  -d '{"force_hour": 42}'
```

### Alert Engine (Kafka Consumer Worker) (Standalone)

The `alert-engine` is a decoupled microservice designed to consume budget thresholds and cost anomaly events from Kafka and route them.

#### Standalone Setup & Execution

An end-user can install and run this package individually by following these steps:

1. **Install the package and dependencies**:
   ```bash
   pip install -e packages/python/alert-engine
   ```

2. **Spin up local infrastructure**:
   This runs PostgreSQL, Redis, and Kafka:
   ```bash
   docker compose -f packages/python/alert-engine/deploy/docker/docker-compose.yaml up -d
   ```

3. **Configure the environment**:
   ```bash
   cp packages/python/alert-engine/.env.example packages/python/alert-engine/.env
   ```

4. **Apply database migrations**:
   Apply SQL migration schemas to PostgreSQL:
   ```bash
   ./packages/python/alert-engine/scripts/migrate.sh
   ```

5. **Run test verification**:
   Verify configuration and end-to-end integration flows:
   ```bash
   ./packages/python/alert-engine/scripts/test.sh
   ```

6. **Start the Kafka Consumer Worker**:
   ```bash
   ./packages/python/alert-engine/scripts/run.sh
   ```

## 3. Implementation Call Chain


| Pipeline Stage | Method Call | Primary File |
| :--- | :--- | :--- |
| **REST API** | `create_app()` | `api/rest/v1/app.py` |
| **Management** | `init_instrumentation()` | `api/rest/v1/handlers/instrumentation.py` |
| **Tracing** | `instrument_app()` | `infra/tracing/middleware.py` |
| **Auto-Capture** | `init_auto_instrumentation()` | `features/auto_instrumentation/index.py` |
| **Decorator** | `@llm_observe` | `features/spans/decorator.py` |
| **Context Manager** | `llm_span()` | `features/manual_instrumentation/service.py` |
| **Orchestration**| `handle_job()` | `worker/index.py` |
| **Logic** | `enrich_span()` | `features/enrich_span/service.py` |
| **Integration** | `create_embedding()` | `infra/clients/cloudflare_embeddings.py` |
| **Identity** | `stable_embedding_key()`| `shared/utils/hash.py` |
| **Token Counting** | `count_tokens()` | `features/token_counting/service.py` |
| **Streaming SDK** | `wrap_async_stream()` | `features/streaming/index.py` |
| **Streaming Logic** | `finalize_stream()` | `features/streaming/service.py` |
| **PII & Injection Scan**| `scan_prompt()` | `features/pii_injection_scan/index.py` |
| **Deterministic Sampling**| `should_sample()` | `features/deterministic_sampling/index.py` |
| **MiniLM Embedding** | `get_embedding()` | `features/minilm_embedding/index.py` |
| **Reliable Reporter** | `report()` / `report_async()` | `infra/adapters/kafka/reliable_adapter.py` |


## Go Tracep SDK & Server

The Go components are located in the [packages/go/tracep](file:///home/btpl-lap-22/live/llm-observability-platform/packages/go/tracep) directory.

### Go Server API Endpoints

The Go Tracep Server automatically multiplexes all operations on a single port in containerized environments like Render (using the `PORT` environment variable) or runs multi-port setups (Ingest on port `4318`, Query on port `4319` by default).

### Live Testing URL
* **Base URL**: [https://tracep-go.onrender.com](https://tracep-go.onrender.com)
* **Cost**: **$0 (100% Free)**. This testing deployment is hosted on Render's Free tier and will not cost you anything.
* **Retention Policy**: All data older than **48 hours (2 days)** is automatically deleted by a background cleanup loop.
* *Note: The instance will spin down (sleep) after 15 minutes of inactivity. The first request after sleep will take around 30-50 seconds to boot up.*

### API Testing Curl Commands

#### 1. Health Check
```bash
curl -i https://tracep-go.onrender.com/health
```

#### 2. Telemetry Ingest (OTLP JSON Payload)
```bash
curl -i -X POST https://tracep-go.onrender.com/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
    "resourceSpans": [
      {
        "scopeSpans": [
          {
            "spans": [
              {
                "traceId": "4f6df6e5f689072a4f6df6e5f689072a",
                "spanId": "4f6df6e5f689072a",
                "name": "test-span",
                "startTimeUnixNano": "1687169400000000000",
                "endTimeUnixNano": "1687169400500000000"
              }
            ]
          }
        ]
      }
    ]
  }'
```

#### 3. List Traces
```bash
curl -i https://tracep-go.onrender.com/traces
```

#### 4. Fetch Single Trace details (Trace ID: `4f6df6e5f689072a4f6df6e5f689072a`)
```bash
curl -i https://tracep-go.onrender.com/traces/4f6df6e5f689072a4f6df6e5f689072a
```

#### 5. Fetch Single Span details (Span ID: `4f6df6e5f689072a`)
```bash
curl -i https://tracep-go.onrender.com/spans/4f6df6e5f689072a
```

#### 6. List Namespaces/Classes
```bash
curl -i https://tracep-go.onrender.com/classes
```

#### 7. List Functions
```bash
curl -i https://tracep-go.onrender.com/functions
```




