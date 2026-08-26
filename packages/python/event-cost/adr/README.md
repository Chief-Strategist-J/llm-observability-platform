# 📐 Event Cost Architecture Decision Records (ADRs)

This directory contains formal Architecture Decision Records (ADRs) for `event-cost`.

---

## 📚 ADR Index

| ADR | Title | Scope / Topics | Status | Date |
|---|---|---|---|---|
| [**0001**](./0001-micro-usd-cost-ledger-and-multi-backend-pricing-engine.md) | Micro-USD Cost Ledger and Multi-Backend Pricing Engine | CostLedger, micro-USD Math, SQLiteBackend, RedisBackend, model_prices.yaml | Accepted | 2026-08-25 |
| [**0002**](./0002-asynchronous-kafka-event-cost-processing-and-persistence.md) | Asynchronous Kafka Event Cost Worker Processing and Persistence Pipeline | Kafka Consumer, llm.spans.raw, Redis Fenwick Trees, Token Bucket, DLQ | Accepted | 2026-08-25 |
