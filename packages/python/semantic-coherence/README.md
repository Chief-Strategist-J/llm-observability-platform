# semantic-coherence

> Layer 3 semantic coherence scorer — multi-model, swappable, production-ready.

---

## Why You Need This

### The Problem

LLMs produce tokens confidently — even when the response is completely off-topic. Standard quality checks (toxicity, PII, latency) tell you *about* the response but never answer the one question that matters operationally:

> **Did the model actually respond to what the user asked?**

A support bot that answers a billing question with a product tutorial has zero coherence. A RAG pipeline returning a document unrelated to the query silently fails. Neither is flagged by existing scorers. Both degrade user trust and silently inflate your evaluation metrics.

### What This Service Does

`semantic-coherence` computes **cosine similarity** between the prompt embedding and response embedding that were already produced by Layer 1 (`queue-embedding-worker`). No re-embedding. No extra model cost. It answers the coherence question for every span in your trace stream.

| What you get | Impact |
|---|---|
| Score ∈ [0, 1] per span | Queryable in your observability stack |
| `LOW_COHERENCE` label per prompt type | Threshold-based alerting out of the box |
| `skipped` flag + `skip_reason` | Honest null instead of a wrong score when PII or embedding is absent |
| All scorer scores in one response | Compare models during calibration without redeploying |

### Why the Architecture Matters to You

**You are calibrating your model.** That means the ground-truth threshold for `LOW_COHERENCE` will shift as your model matures. The similarity model you use today (MiniLM-L6-v2) may be replaced by MPNet, BGE-M3, or a proprietary embed-v3 next quarter.

With a traditional implementation, that change touches the scoring logic, the API, the tests, and the deployment. **With this architecture, it touches zero domain code.** You:

1. Write a new file implementing 3 methods (`name`, `model_id`, `compute`)
2. Register it with one line in `providers.py`
3. Set an env var to promote it as primary

The old scorer keeps running in parallel. You compare scores side-by-side in the API response. When you are satisfied with the new model's production distribution, you update the env var and remove the old file. No migrations. No downtime.

---

## Architecture Overview

```
┌─────────────────────── API Layer ─────────────────────────┐
│  POST /v1/score/semantic-coherence                         │
│  GET  /v1/scorers                                          │
│  GET  /health                                              │
└───────────────────────────┬───────────────────────────────┘
                            │ calls
┌───────────────────────────▼───────────────────────────────┐
│  Domain — score_semantic_coherence()  [zero infra imports] │
│                                                            │
│  1. pii_detected → skip                                    │
│  2. prompt_embedding is None → skip                        │
│  3. response_embedding is None → skip                      │
│  4. for each ScorerPort in registry:                       │
│       raw = scorer.compute(prompt_emb, response_emb)       │
│       score = clamp(raw, 0.0, 1.0)                         │
│       label = classify_coherence(score, prompt_type)       │
└───────────────────────────┬───────────────────────────────┘
                            │ depends on (Protocol only)
┌───────────────────────────▼───────────────────────────────┐
│  ScorerPort  (Protocol — defined by the domain)            │
│  ┌─────────────────────┐  ┌──────────────────────────┐    │
│  │ MiniLMScorerAdapter │  │ YourNextModelAdapter      │    │
│  │ numpy cosine sim    │  │ any impl — just 3 methods │    │
│  └─────────────────────┘  └──────────────────────────┘    │
│                                                            │
│  ScorerRegistry  (named dict — hot-swap by name)           │
└───────────────────────────┬───────────────────────────────┘
                            │ fallback fetch
┌───────────────────────────▼───────────────────────────────┐
│  EmbeddingStorePort  →  EmbeddingWorkerHttpAdapter         │
│  Fetches stored embeddings from Layer 1 by trace+span ID   │
│  One HTTP call. No logic inside.                           │
└────────────────────────────────────────────────────────────┘
```

**Dependency rule:** Arrows always point inward. Nothing in the domain imports infrastructure. Swap any adapter without touching a single domain file.

---

## Threshold Business Rules

These are defined in `src/features/score_semantic_coherence/rules.py` as **first-class named objects** — not magic numbers in an if-statement.

| `prompt_type` | `LOW_COHERENCE` if score < | Rationale |
|---|---|---|
| `chat` | 0.30 | Conversational responses tolerate moderate drift |
| `code` | 0.15 | Code responses can legitimately use different vocabulary |
| `rag` | 0.25 | RAG must stay grounded to retrieved context |
| `classification` | 0.40 | Classification output must tightly match the prompt label space |

When you recalibrate, change the number in `THRESHOLDS`. The test suite (`test_cosine_critical.py`) will catch any boundary regression automatically via parametrized tests against every prompt type.

---

## Environment Variables

| Variable | Default | Required | Description |
|---|---|---|---|
| `EMBEDDING_WORKER_URL` | `http://localhost:8080` | Yes (production) | Base URL of the `queue-embedding-worker` service. Used to fetch stored embeddings when they are not included in the scoring request body. |
| `PRIMARY_SCORER` | `minilm` | No | Name of the scorer whose result is promoted to `primary` in the response. Must match the `name` property of one of the active scorers in `SCORERS`. |
| `SCORERS` | `minilm` | No | Comma-separated list of active scorer names to instantiate at startup (e.g. `minilm,mpnet,bge-small`). Zero code change needed to spin up new scorers! |
| `SCORER_<NAME>_MODEL_ID` | (Resolves to default) | No | Sets the model ID string for a specific scorer name (e.g. `SCORER_MPNET_MODEL_ID=sentence-transformers/all-mpnet-base-v2`). Replaces builtin mappings. |

> **Note:** If `PRIMARY_SCORER` points to a scorer name that is not registered, the service falls back to the first scorer in the registry and logs a warning. No crash, no silent failure.

---

## REST API

### `GET /health`

Returns the service status and the list of registered scorer names.

```json
{
  "status": "ok",
  "scorers": ["minilm"]
}
```

---

### `GET /v1/scorers`

Lists all registered scorer models and the current primary. Use this to verify which models are active before sending calibration requests.

```json
{
  "scorers": [
    { "name": "minilm", "model_id": "sentence-transformers/all-MiniLM-L6-v2" }
  ],
  "primary": "minilm"
}
```

---

### `POST /v1/score/semantic-coherence`

**Request fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `trace_id` | string | Yes | Trace identifier from your observability span |
| `span_id` | string | Yes | Span identifier — used to fetch embeddings if not provided |
| `prompt_type` | `chat` \| `code` \| `rag` \| `classification` | Yes | Determines which threshold is applied for labelling |
| `pii_detected` | boolean | Yes | If `true`, scoring is skipped — no embedding was computed in Layer 1 |
| `prompt_embedding` | float[] | No | 384-dim vector. If absent, fetched from embedding-worker by span |
| `response_embedding` | float[] | No | 384-dim vector. If absent, fetched from embedding-worker by span |
| `scorers` | string[] | No | Names of scorers to run. Omit to run **all registered scorers** (ensemble mode) |
| `primary_scorer` | string | No | Name of the scorer promoted to `primary`. Default: value of `PRIMARY_SCORER` env var |

**Minimal request (embeddings fetched automatically):**

```json
{
  "trace_id": "abc-123",
  "span_id": "def-456",
  "prompt_type": "chat",
  "pii_detected": false
}
```

**Full ensemble request:**

```json
{
  "trace_id": "abc-123",
  "span_id": "def-456",
  "prompt_type": "rag",
  "pii_detected": false,
  "prompt_embedding": [0.12, -0.34, ...],
  "response_embedding": [0.09, -0.31, ...],
  "primary_scorer": "minilm"
}
```

**Response:**

```json
{
  "trace_id": "abc-123",
  "span_id": "def-456",
  "prompt_type": "rag",
  "skipped": false,
  "skip_reason": null,
  "primary": {
    "scorer_name": "minilm",
    "scorer_model": "sentence-transformers/all-MiniLM-L6-v2",
    "score": 0.72,
    "label": "OK",
    "skipped": false,
    "skip_reason": null
  },
  "all_scores": [
    {
      "scorer_name": "minilm",
      "scorer_model": "sentence-transformers/all-MiniLM-L6-v2",
      "score": 0.72,
      "label": "OK",
      "skipped": false,
      "skip_reason": null
    }
  ]
}
```

**Skipped response (PII or missing embedding):**

```json
{
  "trace_id": "abc-123",
  "span_id": "def-456",
  "prompt_type": "chat",
  "skipped": true,
  "skip_reason": "pii_detected",
  "primary": null,
  "all_scores": []
}
```

**`skip_reason` values:**

| Value | Cause |
|---|---|
| `pii_detected` | `pii_detected=true` in request — embedding was never computed in Layer 1 |
| `prompt_embedding_null` | No prompt embedding in request body and embedding-worker returned null |
| `response_embedding_null` | No response embedding in request body and embedding-worker returned null |

---

## Adding or Swapping Scorer Models

### Option A: Zero-Code Dynamic Pluggability (Runtime)

If your new model computes standard cosine similarity on a new or different embedding space, **you do not need to write any code**. Simply define it in your environment:

1. **Add it to `SCORERS`**: Append its name to the comma-separated list (e.g., `SCORERS=minilm,mpnet,bge-small`).
2. **Define its Model ID**: Add the environment variable `SCORER_<NAME>_MODEL_ID` (e.g., `SCORER_BGE_SMALL_MODEL_ID=BAAI/bge-small-en-v1.5`).
3. **Change the Primary (Optional)**: Promote it to the primary by setting `PRIMARY_SCORER=bge-small`.

The service automatically loads it, maps it to the generic `CosineScorerAdapter`, adds it to the ensemble registry, and exposes it in the `/v1/scorers` and `/v1/score/semantic-coherence` APIs.

---

### Option B: Custom Scorer Adapter (Code)

If your model requires custom calculation logic or calls an external service:

```
1. Create: src/infra/adapters/scorers/your_model_scorer.py
2. Implement ScorerPort (3 methods):
      name       → unique string key
      model_id   → full model path (e.g. "org/model-name")
      compute()  → returns float (raw similarity — clamping applied by domain)

3. Register in: src/shared/di/providers.py
      registry.register(YourModelScorerAdapter())

4. Switch primary:
      PRIMARY_SCORER=your-model-name  (env var — no code change)
```

The domain logic, threshold rules, and REST API controllers remain completely **untouched**.

---

## Folder Structure

```
semantic-coherence/
├── src/
│   ├── features/score_semantic_coherence/
│   │   ├── types.py           ← CoherenceInput, CoherenceResult, ScorerOutput, PromptType
│   │   ├── rules.py           ← THRESHOLDS dict, classify_coherence()
│   │   └── service.py         ← score_semantic_coherence() — pure domain
│   ├── shared/
│   │   ├── ports/
│   │   │   ├── scorer_port.py          ← ScorerPort Protocol
│   │   │   └── embedding_store_port.py ← EmbeddingStorePort Protocol
│   │   └── di/
│   │       └── providers.py            ← wires registry + adapters
│   ├── infra/adapters/
│   │   ├── scorers/
│   │   │   ├── minilm_scorer.py    ← MiniLM-L6-v2 cosine adapter
│   │   │   └── scorer_registry.py  ← named registry for multi-model
│   │   └── embedding_worker/
│   │       └── http_adapter.py     ← one HTTP call, zero logic
│   └── api/rest/v1/
│       ├── app.py          ← FastAPI factory + DI wiring
│       ├── router.py
│       └── handlers/
│           ├── score.py    ← POST /v1/score/semantic-coherence
│           ├── scorers.py  ← GET /v1/scorers
│           └── health.py   ← GET /health
├── tests/unit/
│   ├── test_rules.py              ← 9 boundary + completeness tests
│   ├── test_service.py            ← 7 domain flow tests
│   ├── test_skip_conditions.py    ← 5 skip condition tests
│   ├── test_minilm_scorer.py      ← 7 cosine math correctness tests
│   ├── test_scorer_registry.py    ← 6 registry tests
│   ├── test_api.py                ← 11 HTTP contract tests (TestClient)
│   ├── test_cosine_critical.py    ← 15 critical math + boundary tests
│   ├── test_scorer_protocol.py    ← 8 protocol compliance + hot-swap tests
│   └── test_ensemble_divergence.py ← 7 ensemble behaviour tests
├── contracts/openapi/v1.yaml
├── build/Dockerfile
└── deploy/docker/docker-compose.yaml
```

---

## Running Tests

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -v --tb=short
```

**81 tests — 100% pass.**
