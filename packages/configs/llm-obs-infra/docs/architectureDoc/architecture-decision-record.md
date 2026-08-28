# Architecture Decision Record (ADR) Catalog — `llm-obs-infra`

| Field | Value |
|---|---|
| Document ID | ADR-CATALOG-LLMOBS-001 |
| Status | Approved |
| Author(s) | Architecture Steering Committee |
| Target Package | `packages/configs/llm-obs-infra` |
| Date | 2026-08-28 |

---

## Executive Summary

This document provides the consolidated index of key Architectural Decision Records (ADRs) governing choices made within `packages/configs/llm-obs-infra`.

---

## 1. ADR Index

| ADR ID | Title | Status | Summary of Decision |
|---|---|---|---|
| [ADR-0001](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/llm-obs-infra/docs/architectureDoc/architecture-decision-record.md#adr-0001-apache-kafka-kraft-over-zookeeper) | Apache Kafka KRaft Mode | Accepted | Adopt KRaft mode for Kafka to eliminate ZooKeeper container overhead. |
| [ADR-0002](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/llm-obs-infra/docs/architectureDoc/architecture-decision-record.md#adr-0002-google-cloud-alloydb-omni-15) | AlloyDB Omni PostgreSQL Standard | Accepted | Standardize transactional metadata on AlloyDB Omni 15 for ultra-fast query execution. |
| [ADR-0003](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/llm-obs-infra/docs/architectureDoc/architecture-decision-record.md#adr-0003-clickhouse-columnar-span-warehouse) | ClickHouse Columnar Span Warehouse | Accepted | Use ClickHouse `MergeTree` for raw span storage to achieve 8:1 data compression and sub-second analytics. |
| [ADR-0004](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/llm-obs-infra/docs/architectureDoc/architecture-decision-record.md#adr-0004-traefik-v37-ingress-gateway) | Traefik v3.7 Ingress Gateway | Accepted | Deploy Traefik v3.7 with dynamic security middleware for TLS termination and rate limiting. |
| [ADR-0006](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/llm-obs-infra/docs/architectureDoc/infrastructure-resilience-and-edge-case-hardening.md) | Infrastructure Resilience & Edge Case Hardening | Accepted | Implement deterministic system pre-flight verification and active container health polling. |
| [ADR-0007](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/llm-obs-infra/docs/securityDoc/critical-security-remediation-mandate.md) | Critical Security Remediation Mandate | Proposed (Blocking) | Mandatory container bridge isolation, non-root user contexts, and read-only docker socket mounts. |

---

## 2. Core ADR Summaries

### ADR-0001: Apache Kafka KRaft Mode
- **Context**: Standard Kafka setups required a 3-node ZooKeeper cluster, increasing container RAM consumption by over 1GB.
- **Decision**: Upgrade to Kafka KRaft (Kafka Raft Metadata mode).
- **Consequences**: Reduced footprint, simplified container startup, zero ZooKeeper operational overhead.

### ADR-0002: Google Cloud AlloyDB Omni 15
- **Context**: Need standard PostgreSQL syntax with enterprise transactional performance and vector extensions.
- **Decision**: Select `google/alloydbomni:15` as standard relational database.
- **Consequences**: Full PG15 compatibility with 2x–4x performance speedups on complex join queries.

### ADR-0003: ClickHouse Columnar Span Warehouse
- **Context**: Storing raw JSON telemetry spans in PostgreSQL caused massive disk write bottleneck at 10,000 req/sec.
- **Decision**: Deploy ClickHouse v24.8 with `SummingMergeTree` aggregate tables.
- **Consequences**: 87% reduction in disk storage, zero ingest slowdowns, sub-100ms aggregation queries across 50M rows.

---

## 3. Related Documents

- [Infrastructure Resilience and Edge Case Hardening](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/llm-obs-infra/docs/architectureDoc/infrastructure-resilience-and-edge-case-hardening.md)
- [Critical Security Remediation Mandate](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/llm-obs-infra/docs/securityDoc/critical-security-remediation-mandate.md)
