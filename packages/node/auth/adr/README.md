# 📐 Auth Service Architecture Decision Records (ADRs)

This directory contains the formal Architecture Decision Records (ADRs) for `@observability/auth`, detailing High-Level Designs (HLD), Low-Level Designs (LLD), sequence diagrams, component topologies, and architectural trade-offs.

---

## 📚 ADR Index

| ADR | Title | Scope / Topics | Status |
|---|---|---|---|
| [**0001**](./0001-hexagonal-architecture-and-rule-engine-router.md) | Hexagonal Architecture & Declarative Rule Engine Router | Ports & Adapters separation, Rule Engine route matching, OpenTelemetry span wrapping | Accepted |
| [**0002**](./0002-authentication-user-registration-and-signin-flow.md) | Sign-Up, Sign-In, Argon2id Hashing & Audit Logging | Dual-phase authentication flow, Argon2id hash validation, Audit trail capture | Accepted |
| [**0003**](./0003-multi-tenant-organization-switching-and-rls.md) | N-to-N Multi-Tenancy & Org Context Switching | Row-Level Security (RLS), multi-tenant org switching, JWT claim re-issuance | Accepted |
| [**0004**](./0004-session-revocation-redis-token-denylist.md) | Redis Token Denylist & Session Lifetime Management | Server-side JWT session invalidation, Redis O(1) denylist lookup, 401 auto-logout | Accepted |
