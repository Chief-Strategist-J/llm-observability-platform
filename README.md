# LLM Observability Platform: Core Python Infrastructure

This guide covers the technical architecture and end-user usage for the Python-based observability components.

## Table of Contents
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
  - [Prometheus Metrics & Grafana Dashboard](#prometheus-metrics--grafana-dashboard)
  - [Updating Config Files (Model Prices, PII Patterns, Infra)](#updating-config-files-model-prices-pii-patterns-infra)
  - [Docker Deployment](#docker-deployment)
  - [Observability Launcher CLI (llm-observe)](#observability-launcher-cli-llm-observe)
- [3. Implementation Call Chain](#3-implementation-call-chain)

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

### Prometheus Metrics & Grafana Dashboard

The SDK integrates a Prometheus metrics collection pipeline to track operational metrics for LLM calls (latency, TTFT, token usage, cost, and security violations).

#### Configuration & Initialization

Initialize the Prometheus metrics scraping endpoint:

```bash
curl -X POST http://localhost:8000/v1/metrics/init \
  -H "Content-Type: application/json" \
  -d '{"port": 9464}'
```

#### Metrics Endpoints

- **Initialize Pipeline**: `POST /v1/metrics/init`
- **Health Check**: `GET /v1/metrics/health`
- **Record Single Span Metrics**: `POST /v1/metrics/record`
- **Record Batch Spans Metrics**: `POST /v1/metrics/record-batch`

#### Grafana Dashboard

The dashboard is built-in and automatically provisioned on port `3000` (or `3002` in standalone mode). It includes:
- **LLM Latency & TTFT**: Histogram distribution of request latency and time-to-first-token.
- **Token Usage**: Track prompt and completion tokens.
- **Cost Analysis**: Live cost calculation in micro-USD.
- **Security Scans**: Record rates of PII exposure and prompt injections.

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

### Docker Deployments (v1.8.3)

We publish two official Docker images:
* **All-in-One Image (`chiefj/instrumentation-sdk-api`)**: Contains Java, Kafka, PostgreSQL, and pgvector. When started, it automatically initializes database users, databases, runs migrations, and provisions Kafka topics. No external setup required.
* **Standalone Image (`chiefj/instrumentation-sdk-api-nokafka`)**: A lightweight container without the embedded databases and message queues. You supply your own external endpoints.

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


