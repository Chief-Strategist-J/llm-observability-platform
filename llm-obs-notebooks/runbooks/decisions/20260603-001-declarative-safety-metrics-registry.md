# ADR-001 — Declarative Registry Pattern for Instrumentation Metrics

| Field       | Value                                                             |
|-------------|-------------------------------------------------------------------|
| **ID**      | 001                                                               |
| **Date**    | 2026-06-03                                                        |
| **Status**  | accepted                                                          |
| **Deciders**| LLM Observability Platform Team                                   |
| **Package** | `packages/python/instrumentation-sdk`                             |

---

## Context

The `instrumentation-sdk` exposes Prometheus metrics for every LLM span via `MetricsService` and
`PrometheusMetricsAdapter`. Before this ADR, adding a new safety metric (e.g. toxicity detection)
required changes in **four separate files**:

1. `ports.py` — add a new method to the `MetricsPort` Protocol
2. `prometheus_adapter.py` — add a new hardcoded instrument and a new concrete method
3. `service.py` — add a new `if span_data.get(...)` guard and a direct adapter call
4. `test_metrics.py` — add a new mock stub to `_make_adapter()` and a new test case

This is a **CoE (Connascence of Execution)** violation: every consumer of `MetricsPort` must be
updated in lockstep whenever any metric is added. The blast radius of a new metric crosses four
independent units, each with a different reason to change.

### Driving forces

- The platform's safety signal surface is growing (PII → injection → toxicity → jailbreak → hallucination).
- New metrics must not require cross-cutting edits; the change surface must be bounded.
- Test mocks for old adapters must never break when new metrics are added.
- Grafana PromQL expressions must stay automatically consistent with what the adapter emits.

---

## Decision

Introduce a **declarative Safety Metrics Registry** (`registry.py`) as a single source of truth
for all safety/security metric definitions. The registry is a pure-data module with zero
infrastructure imports.

### Structure

```
MetricDefinition(frozen dataclass)
  name: str          ← Prometheus metric name
  metric_type: Enum  ← COUNTER | HISTOGRAM
  description: str
  unit: str

MetricEvaluator(frozen dataclass)
  metric: MetricDefinition
  extract_fn: (span_data) → Optional[(value, labels)]
                  ↑ one function, one job: extract or return None

SAFETY_METRICS_REGISTRY: Tuple[MetricEvaluator, ...]  ← immutable, append-only
```

### Dispatch

`PrometheusMetricsAdapter.__init__` iterates `SAFETY_METRICS_REGISTRY` once and builds an OTel
instrument per `MetricDefinition`. `record_metric(name, value, labels)` dispatches to the correct
instrument via `hasattr(add)` / `hasattr(record)`.

`MetricsService._record()` iterates `SAFETY_METRICS_REGISTRY` after all legacy calls and invokes
`record_metric` behind a `hasattr` guard — backward-compatible with any adapter that does not
implement `record_metric` (e.g. old test mocks).

### Invariant

> **Adding a new safety metric = appending one `MetricEvaluator` to `SAFETY_METRICS_REGISTRY`.**
> No other file changes.

---

## Consequences

### Positive

- **DRY** — metric name, type, description, and extraction logic live in exactly one place.
- **SRP** — `registry.py` has one reason to change: the set of safety metrics changes.
- **Backward compatible** — all 24 pre-existing tests pass unchanged. Old mocks without
  `record_metric` are guarded by `hasattr`.
- **Grafana coherence** — the Prometheus metric name declared in `registry.py` is the exact string
  used in Grafana PromQL, eliminating drift.
- **Testability** — `extract_fn` functions are pure (span dict in, tuple or None out); they are
  unit-tested in isolation with no mocking required.
- **Connascence reduced** — coupling drops from CoE (execution order across 4 files) to CoN
  (name coupling inside one registry file).

### Negative / Trade-offs

- The `hasattr` guard in `service.py` is a structural smell — it exists only for backward
  compatibility with old test mocks that do not implement `record_metric`. This guard will be
  removed once all adapters are updated to implement the full `MetricsPort`.
- `extract_fn` lambdas in a registry lose IDE go-to-definition ergonomics; mitigated by naming
  extractors as module-level functions (`_extract_toxicity_detected`, `_extract_toxicity_score`).
- The registry is a global mutable import; its tuple immutability prevents accidental runtime
  mutation but cannot prevent import-time extension by third parties.

---

## Alternatives Considered

### A — Keep per-metric methods on `MetricsPort` (status quo)

Add `record_toxicity_detected()` and `record_toxicity_score()` as explicit methods.

**Rejected because:** every new metric adds methods to the Protocol, the adapter, and the mock.
The Pattern grows O(N) across N files for each new metric. Connascence of Name × Number of files
is unacceptable at the rate safety signals are being added.

### B — Dynamic metric registration via a `register_metric()` function at startup

Call `registry.register(MetricEvaluator(...))` from each feature's `__init__`.

**Rejected because:** order-of-import dependency introduces CoE (Connascence of Execution).
A declarative tuple requires no initialization order and is easier to reason about in tests.

### C — Separate Prometheus exporter service per feature (PII exporter, Toxicity exporter …)

**Rejected because:** the platform already has a single `instrumentation-sdk` Prometheus endpoint
on port 9464. Multiplying exporter processes for each safety signal increases operational
complexity without proportional benefit at current scale.

---

## Metrics Introduced by this ADR

| Metric Name                    | Type      | Threshold / Logic                               |
|--------------------------------|-----------|-------------------------------------------------|
| `llm_toxicity_detected_total`  | Counter   | `toxicity_score > 0.50` OR `toxicity_detected=True` |
| `llm_toxicity_score`           | Histogram | Raw `[0.0, 1.0]` score per span                 |

---

## Grafana Impact

Dashboard `llm-security-safety-dashboard.json` updated to version 2:

| Panel | Type       | PromQL                                                                          |
|-------|------------|---------------------------------------------------------------------------------|
| 5     | timeseries | `sum(rate(llm_toxicity_detected_total[5m])) by (service_name)`                  |
| 6     | timeseries | `histogram_quantile(0.95, sum(rate(llm_toxicity_score_bucket[5m])) by (le, service_name))` |
| 7     | stat       | `sum(llm_toxicity_detected_total)`                                              |

Panel 3 (Total Security Violations) updated: `+ sum(llm_toxicity_detected_total)`.
Panel 4 (Breakdown bar) updated: `+ Toxicity refId C`.

---

## Test Results

```
42/42 PASSED — 0 regressions
  24 pre-existing tests (test_metrics.py + test_metrics_critical.py)
  18 new tests (test_safety_registry.py)
```

---

## Files Changed

| File | Type |
|------|------|
| `src/features/metrics/registry.py` | NEW |
| `src/features/metrics/ports.py` | MODIFIED |
| `src/features/metrics/index.py` | MODIFIED |
| `src/features/metrics/infra/adapters/prometheus_adapter.py` | MODIFIED |
| `src/features/metrics/service.py` | MODIFIED |
| `tests/unit/features/metrics/test_safety_registry.py` | NEW |
| `build/dashboards/llm-security-safety-dashboard.json` | MODIFIED |

---

## Future Work

When the next safety metric is added (e.g. `llm_jailbreak_attempts_total`):

1. Append one `MetricEvaluator` to `SAFETY_METRICS_REGISTRY` in `registry.py`.
2. Add one `extract_fn` private function in `registry.py`.
3. Add one test class in `test_safety_registry.py`.
4. Add one Grafana panel to `llm-security-safety-dashboard.json`.

Zero changes to `ports.py`, `service.py`, `prometheus_adapter.py`, or existing tests.

---

## References

- [Nygard ADR format](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [MADR](https://adr.github.io/madr/)
- Connascence taxonomy — see `.windsurf/rules/critical.rule.md`
- `packages/python/instrumentation-sdk/src/features/metrics/registry.py`
- `packages/python/instrumentation-sdk/build/dashboards/llm-security-safety-dashboard.json`
- Branch: `feature/toxicity-metrics-registry`
