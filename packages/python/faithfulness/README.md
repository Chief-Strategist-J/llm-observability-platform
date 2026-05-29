# faithfulness

Layer 3 faithfulness scorer for the LLM Observability Platform.

Measures what fraction of response sentences are **entailed** by the retrieved RAG context using DeBERTa-v3-base NLI (`cross-encoder/nli-deberta-v3-base`, 186M parameters).

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI (port 8006)                   │
│  POST /v1/score/faithfulness   GET /health               │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              score_faithfulness() — service              │
│   Pure orchestration. Zero infra imports.                │
│   Calls SentencizerPort → NliScorerPort                  │
└────────────────┬──────────────────┬─────────────────────┘
                 │                  │
    ┌────────────▼──┐    ┌──────────▼─────────────────────┐
    │ SentencizerPort│    │         NliScorerPort           │
    │    (Protocol)  │    │          (Protocol)             │
    └────────────┬──┘    └──────────┬─────────────────────┘
                 │                  │
    ┌────────────▼──┐    ┌──────────▼─────────────────────┐
    │SpacySentencizer│    │      DeBertaNliAdapter          │
    │  en_core_web_sm│    │  cross-encoder/nli-deberta-v3  │
    │   (infra)      │    │  Temperature T=1.5, batch=8    │
    └───────────────┘    └────────────────────────────────┘
```

**Dependency arrows always point inward. Domain never imports infra.**

---

## Algorithm

1. **Skip conditions** — return `score=null` when:
   - `rag_context` is `null` or `< 50` chars
   - `completion_tokens < 10`
   - `finish_reason = "content_filter"`
   - All sentences shorter than 5 words (no qualifying sentences)

2. **Sentence splitting** — spaCy `en_core_web_sm` sentencizer; min 5 words per sentence.

3. **Long-context handling** — if context exceeds 512 words: split into ≤ 400-word chunks; run NLI per sentence against each chunk; take **max entailment probability** across chunks.

4. **NLI scoring** — DeBERTa outputs logits `[contradiction, neutral, entailment]` (order per model config). Temperature T=1.5 applied before softmax. Label = argmax of calibrated probabilities. Batched at 8 pairs/batch.

5. **Score** = `count(entailed sentences) / total_qualifying_sentences`

---

## Skip Conditions Table

| `skip_reason`              | Trigger                                        |
|----------------------------|------------------------------------------------|
| `finish_reason_blocked`    | `finish_reason = "content_filter"`             |
| `rag_context_null`         | `rag_context` is null                          |
| `rag_context_too_short`    | `len(rag_context) < 50`                        |
| `completion_tokens_too_few`| `completion_tokens < 10`                       |
| `no_qualifying_sentences`  | All sentences < 5 words after sentencization   |

When skipped, `score` is `null` and the caller's composite weight for faithfulness (`w_faith = 0.40`) is renormalized to 0.

---

## Environment Variables

| Variable       | Default                           | Description                    |
|----------------|-----------------------------------|--------------------------------|
| `NLI_MODEL_ID` | `cross-encoder/nli-deberta-v3-base` | HuggingFace NLI model ID      |
| `SPACY_MODEL`  | `en_core_web_sm`                  | spaCy pipeline to load         |

---

## API

### `POST /v1/score/faithfulness`

```json
{
  "trace_id": "abc123",
  "span_id": "span456",
  "rag_context": "The Eiffel Tower is located in Paris, France. It was built in 1889.",
  "response_text": "The Eiffel Tower is in Paris. It was constructed in the late 19th century.",
  "completion_tokens": 18,
  "finish_reason": "stop"
}
```

**Response:**

```json
{
  "trace_id": "abc123",
  "span_id": "span456",
  "score": 1.0,
  "skipped": false,
  "skip_reason": null,
  "total_qualifying": 2,
  "entailed_count": 2,
  "sentence_results": [
    {"sentence": "The Eiffel Tower is in Paris.", "label": "entailment", "entailment_prob": 0.912},
    {"sentence": "It was constructed in the late 19th century.", "label": "entailment", "entailment_prob": 0.874}
  ]
}
```

### `GET /health`

```json
{"status": "ok", "model_id": "cross-encoder/nli-deberta-v3-base"}
```

---

## Local Setup

```bash
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
pytest tests/ -v --tb=short
```

---

## Docker

```bash
cd packages/python/faithfulness
bash scripts/deploy_docker.sh
```

Or with docker-compose:

```bash
docker-compose -f deploy/docker/docker-compose.yaml up
```

---

## Latency Budget

| Component            | Typical latency          |
|----------------------|--------------------------|
| spaCy sentencize     | ~2ms per response        |
| NLI per sentence-pair (CPU) | ~48ms           |
| 15 sentences (unbatched) | ~720ms              |
| 15 sentences (batch=8) | ~310ms                |

---

## Composite Score Weight

```
w_faith = 0.40   when faithfulness_score IS NOT NULL
w_faith = 0.00   when faithfulness_score IS NULL (other weights renormalized)
```
