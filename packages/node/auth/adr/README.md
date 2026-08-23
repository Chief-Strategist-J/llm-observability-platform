# 📐 Auth Service Architecture Decision Records (ADRs) & Troubleshooting Guides

This directory contains formal Architecture Decision Records (ADRs) and operational troubleshooting guides for `@observability/auth`, detailing High-Level Designs (HLD), Low-Level Designs (LLD), sequence diagrams, component topologies, TraceQL queries, and architectural trade-offs.

---

## 📚 ADR Index & Guides

| Document | Title | Scope / Topics | Status |
|---|---|---|---|
| [**0001**](./0001-hexagonal-architecture-and-rule-engine-router.md) | Hexagonal Architecture & Declarative Rule Engine Router | Ports & Adapters separation, Rule Engine route matching, OpenTelemetry span wrapping | Accepted |
| [**0002**](./0002-authentication-user-registration-and-signin-flow.md) | Sign-Up, Sign-In, Argon2id Hashing & Audit Logging | Dual-phase authentication flow, Argon2id hash validation, Audit trail capture, Full Call Stack | Accepted |
| [**0003**](./0003-multi-tenant-organization-switching-and-rls.md) | N-to-N Multi-Tenancy & Org Context Switching | Row-Level Security (RLS), multi-tenant org switching, JWT claim re-issuance | Accepted |
| [**0004**](./0004-session-revocation-redis-token-denylist.md) | Redis Token Denylist & Session Lifetime Management | Server-side JWT session invalidation, Redis O(1) denylist lookup, 401 auto-logout | Accepted |
| [**0005**](./0005-opentelemetry-end-to-end-auth-tracing-and-middleware.md) | OpenTelemetry End-to-End Authentication Tracing & Middleware | NodeTracerProvider OTLP exporter, traceHttpMiddleware, W3C trace propagation, Tempo integration | Accepted |
| [**0006**](./0006-kafka-messaging-pipeline-and-distributed-tracing.md) | Kafka Messaging Pipeline & Distributed Tracing Architecture | Centralized Kafka client, Producer/Consumer middleware pipelines, W3C message header propagation | Accepted |
| [**Troubleshooting Guide**](../docs/troubleshooting-and-grafana-guide.md) | Troubleshooting & Grafana Tempo Debugging Guide | TraceQL queries, Grafana setup, time-range filtering, error debugging & fixes | Active Guide |
