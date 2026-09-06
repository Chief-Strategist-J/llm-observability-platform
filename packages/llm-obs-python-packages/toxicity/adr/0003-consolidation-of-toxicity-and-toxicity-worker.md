# ADR 0003: Consolidation of `toxicity` and `toxicity-worker` into a Single Package

| Field | Value |
| --- | --- |
| **ADR ID** | `ADR-PYTHON-TOXICITY-0003` |
| **Title** | Merge `toxicity` and `toxicity-worker` into a Single Unified `toxicity` Package |
| **Status** | **Accepted** |
| **Date** | 2026-08-26 |
| **Scope** | `packages/python/toxicity` — package structure, domain layer, API contract, test consolidation |

---

## 1. Context & Problem Statement

How should we manage the toxicity scoring service when two separate packages existed with **overlapping responsibilities**, **duplicated adapters**, and **diverging module layouts** — making it unclear which was authoritative and which should be deployed?

Previously:

| Package | Role | Problem |
|---|---|---|
| `packages/python/toxicity` | Orchestrator — accepted `trace_id + span_id + response_text`, flagged results, published to Kafka | Owned `features/score_toxicity/` layout; no Prometheus, no warmup |
| `packages/python/toxicity-worker` | Stateless worker — accepted raw `text`, returned raw scores + `long_response_strategy` | Owned `core/domain/` layout; had Prometheus `/metrics`, model warmup, cleaner domain structure |

Both contained:
- An identical `DetoxifyOnnxAdapter` (ONNX model inference).
- An identical `tracer.py` (OTel setup) with only the `service.name` string differing.
- Separate `pyproject.toml` files with partially overlapping deps.
- Separate test suites with no cross-coverage.

---

## 2. Failure Modes We Are Solving

| ID | Symptom | Root Cause | Severity |
|---|---|---|---|
| **FM-01** | Two packages deployed — unclear which is authoritative | No documented ownership boundary | HIGH — ops confusion, split deployments |
| **FM-02** | `DetoxifyOnnxAdapter` duplicated; bug fix must be applied twice | No shared infra layer between packages | MEDIUM — maintenance debt |
| **FM-03** | `toxicity` had no Prometheus metrics; `toxicity-worker` had no Kafka publishing | Capabilities siloed in separate packages | HIGH — neither package was production-complete alone |
| **FM-04** | Separate `pyproject.toml` — dep upgrades diverge silently | Two independent dependency graphs | MEDIUM — transitive version mismatch risk |
| **FM-05** | `toxicity` used `features/score_toxicity/` layout; `toxicity-worker` used `core/domain/` | No agreed domain structure | LOW — cognitive overhead on every PR |

---

## 3. Decision Drivers

- **D1**: One package, one deployment artifact, one `pyproject.toml`.
- **D2**: Domain layout must follow the project standard: `core/domain/` (not `features/`).
- **D3**: Single service must have both capabilities: stateless inference (worker mode) AND Kafka publishing (orchestrator mode).
- **D4**: Publisher must remain optional — controlled by `KAFKA_BOOTSTRAP_SERVERS` env var.
- **D5**: All 23 tests must pass in the merged package without modification to test intent.
- **D6**: Single OpenAPI contract covering both use cases.

---

## 4. Options Considered

### Option A — Keep both packages, create a shared `toxicity-core` library *(rejected)*
- Solves: FM-02 (shared adapter).
- Does not solve: FM-01, FM-03, FM-04, FM-05.
- Creates: third package to maintain, circular import risk.
- **Eliminated**: adds complexity without eliminating the root cause (two deployment targets).

### Option B — Merge `toxicity-worker` into `toxicity`, use `toxicity`'s layout *(rejected)*
- Solves: FM-01, FM-02, FM-03.
- Does not solve: FM-05 (`features/` layout retained).
- **Eliminated**: `features/` layout is non-standard for this project; `core/domain/` is the established pattern.

### Option C — Merge both into `toxicity`, use `toxicity-worker`'s `core/domain/` layout as base *(chosen)*
- Solves: FM-01, FM-02, FM-03, FM-04, FM-05.
- Preserves `toxicity-worker`'s cleaner domain structure and production features (Prometheus, warmup).
- Adds `toxicity`'s Kafka publisher and flagging rules into the merged service.
- Publisher is optional — controlled by env var (D4 satisfied).

---

## 5. Decision Outcome

**Chosen: Option C** — `toxicity-worker`'s architecture used as the base; `toxicity`'s Kafka publisher and flagging rules merged in.

### Final module layout

```
packages/python/toxicity/
├── adr/
│   ├── 0001-onnx-cpu-inference-and-dual-pass-long-text-strategy.md
│   ├── 0002-kafka-publisher-for-flagged-toxicity-events.md
│   ├── 0003-consolidation-of-toxicity-and-toxicity-worker.md
│   └── README.md
├── build/Dockerfile
├── contracts/openapi/v1.yaml          ← unified contract (v2.0.0)
├── deploy/docker/docker-compose.yaml
├── src/
│   ├── core/domain/
│   │   ├── ports/
│   │   │   ├── toxicity_publisher_port.py
│   │   │   └── toxicity_scorer_port.py
│   │   ├── rules.py                   ← from toxicity: TOXICITY_THRESHOLD, is_flagged, determine_flag
│   │   ├── service.py                 ← unified: dual-pass + optional publishing
│   │   └── types.py                   ← unified: ToxicityInput, ToxicityScores, ToxicityResult
│   ├── infra/adapters/
│   │   ├── detoxify_onnx_adapter.py   ← from toxicity-worker (has warmup())
│   │   └── kafka_publisher_adapter.py ← from toxicity (updated imports)
│   ├── api/rest/v1/
│   │   ├── app.py                     ← unified: warmup + Prometheus + optional publisher
│   │   ├── router.py
│   │   └── handlers/
│   │       ├── health.py
│   │       └── score.py               ← unified: text + optional trace_id/span_id or traceparent header
│   └── shared/tracing/tracer.py       ← service.name = "toxicity" (merged)
└── tests/unit/
    ├── test_api.py                    ← 8 async tests (httpx.AsyncClient + ASGITransport)
    ├── test_detoxify_onnx_adapter.py  ← from toxicity-worker
    ├── test_kafka_publisher_adapter.py ← from toxicity (updated imports)
    ├── test_rules.py                  ← from toxicity (updated imports)
    └── test_service.py               ← unified: covers worker mode + orchestrator mode
```

### Unified service behaviour

```
score_toxicity(input, scorer, trace_id=None, span_id=None, publisher=None)
```

| Caller | Publisher arg | Behaviour |
|---|---|---|
| Worker/stateless | `None` | Returns scores + strategy; no Kafka event |
| Orchestrator | `KafkaToxicityPublisherAdapter(...)` | Returns scores + strategy + flagging; publishes to Kafka if `flagged=True` |

### Unified API endpoint

```
POST /score
{
  "text": "...",
  "trace_id": "optional hex string",   ← also accepted via W3C traceparent header
  "span_id":  "optional hex string"
}
```

---

## 6. Failure Modes Created

| ID | Name | Symptom | Detection | Recovery |
|---|---|---|---|---|
| **FM-NEW-01** | Old `POST /v1/score/toxicity` endpoint removed | Callers using old orchestrator endpoint get 404 | Monitor 404 rate after deploy | Update caller to `POST /score` |
| **FM-NEW-02** | `features.score_toxicity` import path removed | Any external code importing old path fails at import | CI lint / import checks | Update all import paths to `core.domain` |

---

## 7. Consequences

### Positive
- **Single deployment**: one Docker image, one `pyproject.toml`, one port.
- **Prometheus `/metrics`** available on the merged service (was only in `toxicity-worker`).
- **Model warmup** on startup prevents cold-start latency on first request.
- **Publisher optional**: `KAFKA_BOOTSTRAP_SERVERS` unset → no-op → local dev works without Kafka.
- **23/23 tests green** after consolidation.
- **Version bumped** to `0.2.0` to signal the breaking API contract change.

### Negative
- **Breaking API change**: `/v1/score/toxicity` replaced by `/score`. Any existing orchestrator callers must be updated.
- **`response_text` field renamed to `text`** in request body. Existing callers must update their payload key.
- Container image size unchanged (same deps, same model).

---

## 8. Deleted Packages

| Package | Commit removed | Replacement |
|---|---|---|
| `packages/python/toxicity-worker` | `2349d4c4` | `packages/python/toxicity` v0.2.0 |
| `packages/python/toxicity-backup` | `2349d4c4` | N/A (pre-merge snapshot) |

---

## 9. Review Trigger

Revisit if:
- A second model (e.g., `unitary/multilingual-toxic-xlm-roberta`) is added — may warrant a model-strategy abstraction layer.
- Worker and orchestrator require **independent scaling** (e.g., worker is CPU-bound at 100% while orchestrator is idle) — re-split at that point is justified.
- Prometheus scrape cadence or metric cardinality causes memory growth > 100 MB — extract metrics to a sidecar.
