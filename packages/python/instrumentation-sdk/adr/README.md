# 📐 Python Instrumentation SDK Architecture Decision Records (ADRs)

This directory contains formal Architecture Decision Records (ADRs) for `instrumentation-sdk`, detailing High-Level Designs (HLD), Low-Level Designs (LLD), sequence diagrams, component topologies, and architectural trade-offs.

---

## 📚 ADR Index

| ADR | Title | Scope / Topics | Status |
|---|---|---|---|
| [**0001**](./0001-centralized-kafka-and-api-key-verification.md) | Centralized Kafka Infrastructure & API Key Verification | KafkaBrokerConfig, KafkaClientFactory, ApiKeyDomainService, StandardRequestContextMiddleware, CORS | Accepted |
