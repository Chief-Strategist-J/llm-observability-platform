# Contract Changelog

All changes to the contract definitions (`openapi`, `asyncapi`, `proto`, `graphql`, `registries`) will be documented here.

## [2.0.0] - 2026-08-26

### Added
- **Declarative Architecture Schemas**: Added `schema/auto_instrumentation_schema.py` and `rules/rules.py` mapping specifications.
- **OpenTelemetry GenAI Semantic Conventions (`gen_ai.*`)**: Standardized span attributes for input/output tokens, cost in micro-USD (`gen_ai.usage.cost_micro_usd`), provider (`gen_ai.provider.name`), and session context (`gen_ai.conversation.id`).
- **Centralized Infrastructure Configurations**: Consolidated environment configurations under `config/infra/infra_constants.py` matching `packages/configs/llm-obs-infra`.
