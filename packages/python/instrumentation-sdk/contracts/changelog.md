# Changelog
All notable changes to the `instrumentation-sdk` package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2026-05-19

### Added
- **PII & Injection Scanning (Aho-Corasick & Regex Fallback)**: Added prompt scanning for structural PII patterns and jailbreak/injection phrases.
- **REST API Endpoint**: Exposed `POST /v1/pii-injection/scan` to allow remote scanning.
- **Contract-First Support**: Added `/pii-injection/scan` path definition to the OpenAPI v1.yaml contract.  

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
- **CI/CD**: Added automated contract and integration tests in `.github/workflows/instrumentation-sdk-contract.yml`.

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
### Added
- Initial release of the `instrumentation-sdk`.
- Core auto-instrumentation patchers for OpenAI, Anthropic, LiteLLM, and LangChain.
- `@llm_observe` decorator and `llm_span` context manager.
- Background worker for span enrichment and Cloudflare AI integration.
