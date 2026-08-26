# 📐 Python Instrumentation SDK Architecture Decision Records (ADRs)

This directory contains formal Architecture Decision Records (ADRs) for `instrumentation-sdk`, detailing High-Level Designs (HLD), Low-Level Designs (LLD), sequence diagrams, component topologies, and architectural trade-offs.

---

## 📚 ADR Index

| ADR | Title | Scope / Topics | Status |
|---|---|---|---|
| [**0001**](./0001-centralized-kafka-and-api-key-verification.md) | Centralized Kafka Infrastructure & API Key Verification | KafkaBrokerConfig, KafkaClientFactory, ApiKeyDomainService, StandardRequestContextMiddleware, CORS | Accepted |
| [**0002**](./0002-telemetry-ingestion-and-cost-engine-integration.md) | Telemetry Ingestion Pipeline and Event Cost Engine Integration | Span Ingestion, event-cost, event-cost-worker, SQLite WAL, Micro-USD Costs | Accepted |
| [**0003**](./0003-declarative-rules-engine-and-genai-conventions.md) | Declarative Rules Engine & OpenTelemetry GenAI Semantic Conventions | DeclarativeRulesEngine, OTEL GenAI Conventions (`gen_ai.*`), Hexagonal Adapters, Data/Logic Separation | Accepted |
| [**0004**](./0004-consolidated-kafka-messaging-and-middleware-pipeline-architecture.md) | Consolidated Kafka Messaging & Middleware Pipeline Architecture | `src/infra/messaging/`, Producer & Consumer Middleware, W3C Context Propagation, DLQ Routing, CQRS Projections | Accepted |
