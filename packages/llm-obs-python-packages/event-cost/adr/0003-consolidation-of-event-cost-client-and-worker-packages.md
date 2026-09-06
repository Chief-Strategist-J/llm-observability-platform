# ADR 0003: Consolidation of Event Cost Client and Worker Packages

| Field | Value |
| --- | --- |
| **ADR ID** | `ADR-PYTHON-EVENT-COST-0003` |
| **Title** | Consolidation of Event Cost Client Library and Worker Packages |
| **Status** | **Accepted** |
| **Date** | 2026-08-26 |
| **Scope** | Unified Package Structure (`event-cost`), Standard `package-structure.md` Layout (`src/{features, handlers, infra, shared, worker}`) |

---

## 1. Context & Problem Statement

Previously, cost engine functionality was split across two separate packages in `packages/python/`:
1. `packages/python/event-cost`: Python client library providing `CostLedger`, SQLite, and basic Redis backends.
2. `packages/python/event-cost-worker`: Asynchronous Kafka consumer service for Fenwick tree aggregation and token bucket reconciliation.

This split created several architectural friction points:
- **Tight Coupling & Hacked Paths**: `event-cost` unit tests explicitly relied on adding `../event-cost-worker/src` to its `pythonpath`.
- **Duplicated Redis Adapters**: Both packages defined separate implementations for Redis Fenwick tree updates, token bucket deductions, and deduplication logic.
- **Fragmented Packaging**: Managing dependencies, versioning, container builds, and deployment manifests required maintaining two parallel `pyproject.toml` configurations.

---

## 2. Decision Outcome

We merged `event-cost-worker` directly into `event-cost` and aligned the folder structure strictly with the workspace-wide **[package-structure.md](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/folderStructure/package-structure.md)** rule.

### Key Architectural Decisions:
1. **Root Package**: Single distribution package `event-cost` in `pyproject.toml`.
2. **Canonical Sub-package Layout** (`src/`):
   - `src/features/cost_ledger`: Ledger domain logic (`ledger.py`, `backends/`, `prices/`).
   - `src/handlers/llm_spans_raw`: Domain event processing handlers.
   - `src/infra/adapters/metrics`: Observability adapters (`PrometheusAdapter`).
   - `src/shared`: Shared types, ports, contract validators, and utility functions (`retry.py`).
   - `src/worker`: Ingestion worker entrypoint (`index.py`), config (`config.py`), and registry (`registry.py`).
3. **DRY Guardrail & Standard Placement**: Removed intermediate `src/event_cost/` nesting to conform to universal layout rules across all 19 Python workspace packages.
4. **Gitkeep Rule Enforcement**: Added `.gitkeep` files in every subdirectory per Rule 3 of `package-structure.md`.
5. **Test Consolidation**: Consolidated unit and integration tests under top-level `tests/`.

---

## 3. Revised Package Structure

```text
packages/python/event-cost/
├── adr/
│   ├── 0001-micro-usd-cost-ledger-and-multi-backend-pricing-engine.md
│   ├── 0002-asynchronous-kafka-event-cost-processing-and-persistence.md
│   ├── 0003-consolidation-of-event-cost-client-and-worker-packages.md
│   └── README.md
├── build/
│   └── Dockerfile
├── contracts/
│   └── events/
│       ├── llm_spans_raw.yaml
│       └── changelog.md
├── database/
│   ├── migrations/
│   └── schema.lock
├── deploy/
│   └── docker/
│       └── docker-compose.yaml
├── scripts/
│   ├── deploy_docker.sh
│   ├── health-check.sh
│   ├── migrate.sh
│   ├── run.sh
│   └── test.sh
├── src/
│   ├── __init__.py
│   ├── features/
│   │   └── cost_ledger/
│   │       ├── backends/
│   │       ├── prices/
│   │       └── ledger.py
│   ├── handlers/
│   │   └── llm_spans_raw/
│   ├── infra/
│   │   └── adapters/metrics/
│   ├── shared/
│   │   ├── contracts/
│   │   ├── ports/
│   │   ├── types/
│   │   └── utils/
│   └── worker/
│       ├── config.py
│       ├── index.py
│       └── registry.py
├── tests/
├── pyproject.toml
└── README.md
```

---

## 4. Consequences

### Positive Consequences
- **Strict Policy Compliance**: Aligns 100% with repo-wide `package-structure.md` rules.
- **Single Source of Truth**: Unified dependency graph, versioning (`0.2.0`), and pyproject config.
- **Zero Cross-Package Import Hacks**: Eliminates relative parent path additions (`../event-cost-worker/src`).
- **Clean Developer Experience**: Monorepo developers and worker docker containers build from a standard `src/` tree.
