# Changelog

All notable changes to the `instrumentation-sdk` package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.11.0] - 2026-06-05

### Added
- **NLI Scorer Worker Package**: A stateless microservice (`nli-worker`) using the `cross-encoder/nli-deberta-v3-base` model to score sentence-pairs for natural language inference (NLI) and calculate LLM faithfulness. Features context chunking for contexts exceeding 400 tokens, batched NLI scoring, temperature-scaled softmax calibration (T=1.5), and OpenTelemetry trace propagation.
- **Model Registry & Weight Decoupling (ADR-004)**: Decoupled model weight storage from the `nli-worker` CPU/GPU container runtimes to optimize image sizes (< 1GB for CPU) and enable runtime hot-swapping of natural language inference models. Implemented memory-caching of model and tokenizer instances within [NliScorerAdapter](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker/src/infra/adapters/nli_scorer_adapter.py), parameterized REST endpoints in [nli.py](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker/src/api/rest/v1/handlers/nli.py) to accept dynamic `model_id` payloads, introduced [NliScorerPort](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker/src/core/domain/ports/nli_scorer_port.py) for Clean Architecture decoupling, and implemented lifespan startup preloading in [app.py](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker/src/api/rest/v1/app.py) to mitigate first-request cold-starts. Detailed architectural design is documented in [ADR-004](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/decisions/20260605-004-nli-worker-decoupling.md).
- **Verification Scripts**: Added a repository-wide shell script audit utility [bash-audit.sh](file:///home/btpl-lap-22/live/obs/scripts/bash-audit.sh) to automatically verify executable permissions, shebang headers, syntax correctness, and safety/fail-on-error configurations for all project shell scripts.

## [1.10.0] - 2026-05-29

### Added
- **Toxicity Scorer Package**: Multi-label toxicity classifier microservice using `unitary/toxic-bert` ONNX running on CPU. Includes a dual-pass evaluation window strategy for texts > 512 tokens and automatically publishes flagged toxic responses (score > 0.50) to the `llm.toxicity.flagged` Kafka topic.
- **Faithfulness Scorer Package**: Hallucination detection microservice utilizing `cross-encoder/nli-deberta-v3-base` to check sentence entailment against retrieved RAG contexts. Features temperature scaling (T=1.5), sentence splitting with spaCy, context chunking, and OpenTelemetry trace propagation.
- **Semantic Coherence Scorer Package**: Evaluation microservice to check prompt-to-response relevance via cosine similarity of pre-computed embeddings. Supports multiple prompt types (chat, code, rag, classification) with distinct thresholds, and a dynamically swappable scorer registry.
- **REST Endpoints Enrichment**: Added span ingestion (`POST /spans`), fallback chain tracking (`/fallback/track`, `/fallback/clear`), tool call tracking (`/tool-call/track`, `/tool-call/clear`), and price database fetching/reloading (`/metrics/prices`, `/metrics/prices/reload`).

## [1.9.0] - 2026-05-28

### Added
- **Alert Engine Package**: Decoupled Python-based Kafka consumer worker to route and dedup budget alerts and cost anomalies to PostgreSQL, Slack, and PagerDuty endpoints.
- **Budget Threshold Alerts**: Deduplicated budget warnings and blocks (15-minute Redis rate-limiting suppression window) with automatic Slack channel routing and service owner DMs.
- **Cost Anomaly Routing**: Intraday cost spike alerting comparing current costs against EWMA baselines, routing to Slack drill-down clusters and PagerDuty incidents with automatic cold start suppression.
- **OpenTelemetry Context Propagation**: Automatic trace context extraction using W3C traceparent standards from incoming Kafka headers to link alert routing actions as child spans of LLM operations.
- **Container Deployment Support**: Dockerfile and multi-service docker-compose.yaml for standalone deployment of alert-engine and its dependencies.

## [1.8.2] - 2026-05-23

### Added
- **Multi-Model Fallback Chain Tracking**: Correlates multiple retry attempts under a single request trace by passing `attempted_models` and `retry_count` through the SDK manual span enrichment pipeline and the REST API span ingestion endpoint.
- **Tool-Call Chain Linking**: Expose `/v1/tool-call/track` and `/v1/tool-call/clear` API endpoints. Intercept 'tool_calls' finish reason to emit intermediate transition spans and track cumulative trace cost.
- **Optimization of Kafka Reporter WAL**: Offloaded Protobuf serialization to a background thread to prevent thread contention, and optimized local SQLite Write-Ahead Log (WAL) fallback writing.
- **OTel Performance Benchmarking**: Added profiling tools to benchmark memory/CPU footprints of the telemetry pipeline.

### Fixed
- **Docker Startup Delay**: Delay downstream services startup in all-in-one `entrypoint.sh` to avoid resource contention during Grafana database migrations.

## [1.8.1] - 2026-05-22

### Fixed
- Bumped version to 1.8.1 to resolve PyPI package release collision.

## [1.7.0] - 2026-05-21

### Added
- **MiniLM Embedding Integration**: Asynchronous, non-blocking fetch of MiniLM embeddings for prompts concurrently with span finalization using `asyncio.create_task()`.
- **REST API Endpoint**: Exposed `POST /v1/embeddings/embed` to generate embeddings for arbitrary text via the embedding worker.
- **Contract-First Support (Embedding)**:
  - **OpenAPI**: Added `/embeddings/embed` endpoint to `v1.yaml`.
  - **GraphQL**: Added `getEmbedding` query and `GetEmbeddingPayload` to `v1.graphql`.
  - **Protobuf**: Added `GetEmbedding` RPC, request, and response message schemas to `instrumentation.proto`.

## [1.6.0] - 2026-05-21

### Added
- **Deterministic Sampling Gate**: Hashing of `span_id` using SHA256 modulo 100 to determine if span should be sampled (`is_sampled = True`). Prevents expensive operations (hashing/embeddings) when unsampled.
- **REST API Endpoint**: Exposed `POST /v1/sampling/should-sample` to check if a span should be sampled.
- **Contract-First Support (Sampling)**:
  - **OpenAPI**: Added `/sampling/should-sample` path definition to `v1.yaml`.
  - **GraphQL**: Added `shouldSample` query and `SamplingGatePayload` structure to `v1.graphql`.
  - **Protobuf**: Added `ShouldSample` RPC, request, and response message schemas to `instrumentation.proto`.
- **Performance Load Test Suite** (`tests/performance/test_metrics_load.py`): 7 pytest cases covering 100 individual spans, 10×50 batch spans, mixed error ratios, PII/injection flags, all model/provider combos, and high token counts. Marked `@pytest.mark.performance` — excluded from unit/integration CI by default.
- **Grafana Config CI** (`.github/workflows/grafana-config-validate.yml`): File-targeted CI that triggers **only** on changes to these exact 10 files: `grafana-datasource.yaml`, `grafana-dashboard-provider.yaml`, `prometheus.yml`, `tempo-config.yaml`, all 4 dashboard JSON files, `model_prices.yaml`, and `patterns.yaml`. Validates YAML syntax, required fields, dashboard UID uniqueness, regex compilability, and price-entry integrity. No Docker — runs in ~60 s.
- **Prometheus Metrics collection & scraping**: Integrated OpenTelemetry Prometheus adapter to collect operational metrics from LLM call lifecycles.
- **REST Metrics API**: Exposed endpoints `POST /v1/metrics/init`, `GET /v1/metrics/health`, `POST /v1/metrics/record`, and `POST /v1/metrics/record-batch` for metrics orchestration.
- **Grafana Dashboard**: Provisioned Grafana dashboard visualizing LLM latency, TTFT, token usage, cost, and error rates.
- **Contract-First Support (Metrics)**:
  - **OpenAPI**: Added OpenAPI routes and schemas for the metrics endpoints.
  - **GraphQL**: Exposed `initMetrics`, `recordMetrics`, `recordMetricsBatch` mutations and `metricsHealth` query.
  - **Protobuf**: Added `InitMetrics`, `GetMetricsHealth`, `RecordMetrics`, `RecordMetricsBatch` RPCs to `InstrumentationControlService`.

### Fixed
- **Grafana "database is locked" crash**: Set `GF_DATABASE_WAL=true` permanently in `entrypoint.sh`. Root cause: a manual debug run had initialised the SQLite DB in WAL mode; subsequent container starts without WAL=true caused the migration service to crash silently, leaving port 3000 unreachable.
- **Proto buf lint failures**: Split shared `MetricsStatusResponse` into `InitMetricsResponse` and `GetMetricsHealthResponse` so each RPC has a uniquely named response type — satisfying `buf lint` naming and reuse rules.

### Runbook — Config File Changes Require Container Restart

| File changed | Action required |
|---|---|
| `config/model_prices.yaml` | Restart container: `docker restart instrumentation-sdk-api` |
| `config/patterns.yaml` | Restart container: `docker restart instrumentation-sdk-api` |
| `build/grafana-datasource.yaml` | Restart container |
| `build/grafana-dashboard-provider.yaml` | Restart container |
| `build/prometheus.yml` | Restart container |
| `build/tempo-config.yaml` | Restart container |
| `build/dashboards/*.json` | Hot-reloaded by Grafana every 30 s — no restart needed |

## [1.5.0] - 2026-05-19

### Added
- **PII & Injection Scanning (Aho-Corasick & Regex Fallback)**: Added prompt scanning for structural PII patterns and jailbreak/injection phrases.
- **REST API Endpoint**: Exposed `POST /v1/pii-injection/scan` to allow remote scanning.
- **Contract-First Support**:
  - **OpenAPI**: Added `/pii-injection/scan` path definition to the OpenAPI `v1.yaml` contract.
  - **GraphQL**: Added `scanPiiInjection` query and `PiiInjectionScanPayload` structure to `v1.graphql`.
  - **Protobuf**: Added `ScanPiiInjection` RPC, request, and response message schemas to `instrumentation.proto`.

## [1.4.0] - 2026-05-18

### Added
- **All-in-One Standalone Telemetry & API Container**: Bundled the FastAPI API server, Grafana, and Tempo inside a single, unified Docker image.
  - Automatically provisions Tempo as a read-only trace datasource at container startup.
  - Ephemeral block and WAL storage configured under `/tmp/tempo` inside the container.
  - Orchestrates background Tempo, Grafana, and frontend Uvicorn processes seamlessly via `entrypoint.sh`.
  - Pushed to Docker Hub registry as a production-ready image under the tag `chiefj/instrumentation-sdk-api:unstable` for one-command user deployment.

## [1.3.0] - 2026-05-18

### Added
- **Streaming Observability (TTFT & Token Tracking)**: Implemented specialized utilities for tracking streaming LLM calls (both sync and async generators).
  - Automatically captures **Time-to-First-Token (TTFT)** latency at the exact moment of the first yielded chunk.
  - Accumulates yielded chunks and calculates completed completion tokens upon stream completion, close, or failure.
  - Defers manual span finalization until the stream has completed, offering full resilience to early consumer aborts (`.close()` and `.aclose()`).
- **REST API Endpoint**: Exposed `POST /v1/streaming/test-stream-call` to verify streaming and TTFT tracking.
- **Contract-First Support**:
  - **GraphQL**: Added `triggerTestStreamCall` mutation.
  - **Protobuf**: Added `TriggerTestStreamCall` RPC and `TriggerTestStreamCallRequest` message structure.
  - **OpenAPI**: Added `/streaming/test-stream-call` path definition to `v1.yaml`.

## [1.2.0] - 2026-05-18

### Added
- **Token Counting**: Implemented pre-call token counting utilizing `tiktoken` with fallback character-based heuristics.
  - Supports plain text string prompts, complex nested chat message lists, and OpenAI tile-based vision token calculation with pure-Python PNG/JPEG/GIF dimension parsing.
  - Automatically records `prompt_tokens` and `token_count_method` inside manual spans via `llm_span_with_tokens`.
- **REST API Endpoint**: Exposed `POST /v1/token-counting/count` to allow remote token calculation.
- **Contract-First Support**: Added `/token-counting/count` path definition to the OpenAPI v1.yaml contract.

### Changed
- **Public API Namespace**: Exposed `count_tokens` and `llm_span_with_tokens` directly at the package root level.

## [1.1.0] - 2026-05-15

### Added
- **REST API Layer**: Implemented a FastAPI-based management API for remote orchestration.
  - `POST /instrumentation/init`: Remotely enable auto-instrumentation.
  - `POST /instrumentation/uninstrument`: Disable all active patchers.
  - `POST /instrumentation/detect`: Dry-run detection of LLM providers from request samples.
  - `POST /instrumentation/test-call`: End-to-end tracing verification.
- **Observability Integration**: Injected OpenTelemetry (OTEL) middleware for standardized trace collection.
- **Contract-First Support**:
  - **Protobuf**: Added `InstrumentationService` with `Init`, `Uninstrument`, `DetectProvider`, and `TriggerTestCall` RPCs.
  - **GraphQL**: Added `initInstrumentation`, `uninstrument`, and `detectProvider` mutations.
  - **AsyncAPI**: Introduced `llm.instrumentation.events` channel for state change notifications.
- **Docker Infrastructure**:
  - Production, Development, and Testing Dockerfiles with optimized layer caching.
  - Multi-environment Docker Compose configurations (`dev`, `prod`, `test`).
  - Automated contract and integration tests.

### Changed
- **Architecture**: Migrated to a feature-isolated structure following Hexagonal Architecture principles.
- **Middleware**: Refactored `tracer_provider` isolation to support side-effect-free testing.

### Fixed
- **Kafka Provisioning**: Added missing `llm.instrumentation.events` topic to the automated setup scripts and docker-compose configurations, resolving integration test failures.
- **API Initialization**: Fixed a critical bug where the FastAPI `app` instance was not defined when `SKIP_APP_INIT` was set, preventing the container from starting.

### Security
- Added manual span attribute injection for protected services.
- Isolated test telemetry using `InMemorySpanExporter` to prevent global state contamination.

## [1.0.0] - 2026-05-10
- Initial release of the `instrumentation-sdk`.
- Core auto-instrumentation patchers for OpenAI, Anthropic, LiteLLM, and LangChain.
- `@llm_observe` decorator and `llm_span` context manager.
- Background worker for span enrichment and Cloudflare AI integration.
