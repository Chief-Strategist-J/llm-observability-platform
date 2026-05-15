# Changelog
All notable changes to the `instrumentation-sdk` package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

### Security
- Added manual span attribute injection for protected services.
- Isolated test telemetry using `InMemorySpanExporter` to prevent global state contamination.

## [1.0.0] - 2026-05-10
### Added
- Initial release of the `instrumentation-sdk`.
- Core auto-instrumentation patchers for OpenAI, Anthropic, LiteLLM, and LangChain.
- `@llm_observe` decorator and `llm_span` context manager.
- Background worker for span enrichment and Cloudflare AI integration.
