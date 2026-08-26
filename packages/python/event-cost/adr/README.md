# 📐 Event Cost Architecture Decision Records (ADRs)

This directory contains formal Architecture Decision Records (ADRs) for `event-cost`.

---

## 📚 ADR Index

| ADR | Title | Scope / Topics | Status | Date |
|---|---|---|---|---|
| [**0001**](./0001-micro-usd-cost-ledger-and-multi-backend-pricing-engine.md) | Micro-USD Cost Ledger and Multi-Backend Pricing Engine | CostLedger, micro-USD Math, SQLiteBackend, RedisBackend, model_prices.yaml | Accepted | 2026-08-25 |
| [**0002**](./0002-asynchronous-kafka-event-cost-processing-and-persistence.md) | Asynchronous Kafka Event Cost Worker Processing and Persistence Pipeline | Kafka Consumer, llm.spans.raw, Redis Fenwick Trees, Token Bucket, DLQ | Accepted | 2026-08-25 |
| [**0003**](./0003-consolidation-of-event-cost-client-and-worker-packages.md) | Consolidation of Event Cost Client Library and Worker Packages | Package Merger, Namespace Topology, Single pyproject.toml, Test Consolidation | Accepted | 2026-08-26 |
| [**0004**](./0004-sdk-ingestion-frontend-integration-and-database-schema-design.md) | SDK Ingestion, Frontend Integration, and Analytical Database Schema Design | SDK Ingestion, Next.js Dashboard API, PostgreSQL Partitions & Redis Key Layout | Accepted | 2026-08-26 |
| [**0005**](./0005-fault-tolerant-messaging-topology-and-failure-recovery.md) | Fault-Tolerant Asynchronous Messaging Topology and Failure Recovery Architecture | Kafka Consumer Retention, Offset Commits, Redis Dedup Guard & DLQ Isolation | Accepted | 2026-08-26 |
