# Changelog
All notable changes to the `instrumentation-sdk` package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
