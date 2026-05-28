# semantic-coherence

Layer 3 semantic coherence scorer. Computes cosine similarity between prompt and response embeddings reused from Layer 1 (`queue-embedding-worker`). Supports **multi-model ensemble** and **hot-swap** via the `ScorerPort` registry.

---

## Folder Structure

```
semantic-coherence/
├── src/
│   ├── features/score_semantic_coherence/
│   │   ├── types.py           ← CoherenceInput, CoherenceResult, ScorerOutput, PromptType
│   │   ├── rules.py           ← THRESHOLDS dict, classify_coherence() — first-class business rules
│   │   └── service.py         ← score_semantic_coherence() — pure domain, zero infra imports
│   ├── shared/
│   │   ├── ports/
│   │   │   ├── scorer_port.py         ← ScorerPort Protocol (swappable model contract)
│   │   │   └── embedding_store_port.py ← EmbeddingStorePort Protocol
│   │   └── di/
│   │       └── providers.py           ← builds ScorerRegistry + EmbeddingStorePort
│   ├── infra/
│   │   └── adapters/
│   │       ├── scorers/
│   │       │   ├── minilm_scorer.py   ← MiniLM-L6-v2 cosine scorer (implements ScorerPort)
│   │       │   └── scorer_registry.py ← named registry for multi-model ensemble
│   │       └── embedding_worker/
│   │           └── http_adapter.py    ← one HTTP call to embedding-worker (no logic)
│   └── api/rest/v1/
│       ├── app.py             ← FastAPI factory + DI wiring
│       ├── router.py          ← composes all v1 routes
│       └── handlers/
│           ├── score.py       ← POST /v1/score/semantic-coherence
│           ├── scorers.py     ← GET /v1/scorers
│           └── health.py      ← GET /health
├── tests/unit/
│   ├── test_rules.py
│   ├── test_service.py
│   ├── test_skip_conditions.py
│   ├── test_scorer_registry.py
│   └── test_minilm_scorer.py
├── contracts/openapi/v1.yaml
├── build/Dockerfile
└── deploy/docker/docker-compose.yaml
```

---

## Decision Tree

```
score_semantic_coherence()
│
├── pii_detected=TRUE ──────────────────────────────→ score=null, skip_reason=pii_detected
│
├── prompt_embedding IS NULL ───────────────────────→ score=null, skip_reason=prompt_embedding_null
│
├── response_embedding IS NULL ─────────────────────→ score=null, skip_reason=response_embedding_null
│
└── all valid
    │
    └── for each scorer in ScorerRegistry
        │
        ├── scorer.compute(prompt_emb, response_emb) → raw float
        ├── clamp to [0, 1]
        └── classify_coherence(score, prompt_type)
            ├── score < THRESHOLDS[prompt_type] → LOW_COHERENCE
            └── score >= THRESHOLDS[prompt_type] → OK
```

---

## Thresholds

| prompt_type      | LOW_COHERENCE if score < |
|------------------|--------------------------|
| `chat`           | 0.30                     |
| `code`           | 0.15                     |
| `rag`            | 0.25                     |
| `classification` | 0.40                     |

---

## Adding a New Scorer Model

1. Create `src/infra/adapters/scorers/<your_model>_scorer.py`
2. Implement the `ScorerPort` Protocol:
   ```python
   class YourModelScorerAdapter:
       @property
       def name(self) -> str: return "your-model"
       @property
       def model_id(self) -> str: return "org/your-model-name"
       def compute(self, prompt_embedding, response_embedding) -> float: ...
   ```
3. Register it in `src/shared/di/providers.py`:
   ```python
   registry.register(YourModelScorerAdapter())
   ```
4. Set `PRIMARY_SCORER=your-model` env var to promote it as primary.

No domain code changes required.

---

## REST API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + registered scorer names |
| `GET` | `/v1/scorers` | List all registered scorers and current primary |
| `POST` | `/v1/score/semantic-coherence` | Score coherence between prompt and response |

### POST /v1/score/semantic-coherence

**Request:**
```json
{
  "trace_id": "abc-123",
  "span_id": "def-456",
  "prompt_type": "chat",
  "pii_detected": false,
  "prompt_embedding": [0.1, 0.2, ...],
  "response_embedding": [0.1, 0.2, ...],
  "scorers": ["minilm"],
  "primary_scorer": "minilm"
}
```

- `prompt_embedding` / `response_embedding` — optional. If absent, fetched from embedding-worker via `trace_id` + `span_id`.
- `scorers` — optional list of scorer names. Omit to run **all registered scorers** (ensemble mode).
- `primary_scorer` — name of scorer whose result is promoted as primary output.

**Response:**
```json
{
  "trace_id": "abc-123",
  "span_id": "def-456",
  "prompt_type": "chat",
  "skipped": false,
  "skip_reason": null,
  "primary": {
    "scorer_name": "minilm",
    "scorer_model": "sentence-transformers/all-MiniLM-L6-v2",
    "score": 0.82,
    "label": "OK",
    "skipped": false,
    "skip_reason": null
  },
  "all_scores": [
    {
      "scorer_name": "minilm",
      "scorer_model": "sentence-transformers/all-MiniLM-L6-v2",
      "score": 0.82,
      "label": "OK",
      "skipped": false,
      "skip_reason": null
    }
  ]
}
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_WORKER_URL` | `http://localhost:8080` | Base URL of the embedding-worker service |
| `PRIMARY_SCORER` | `minilm` | Name of the primary scorer |

---

## Running Tests

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -v --tb=short
```

34 tests — 100% pass rate.
