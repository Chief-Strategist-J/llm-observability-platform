# faithfulness

> **Layer 3 Faithfulness Scorer** — *Did the LLM make things up, or stay grounded in context?*

DeBERTa-v3-base NLI (`cross-encoder/nli-deberta-v3-base`, 186M parameters)  
Entailment fraction over retrieved RAG context · FastAPI · Port **8006**

---

## ⚡ 5-Minute Quickstart

```bash
# 1. Pull and run
docker pull chiefj/faithfulness:latest
docker run -p 8006:8006 chiefj/faithfulness:latest

# 2. Check it's alive
curl http://localhost:8006/health

# 3. Score a response
curl -s -X POST http://localhost:8006/v1/score/faithfulness \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "trace-001",
    "span_id":  "span-001",
    "rag_context": "The Eiffel Tower is located in Paris, France. It was built in 1889 by Gustave Eiffel.",
    "response_text": "The Eiffel Tower is in Paris. It was built in 1889.",
    "completion_tokens": 14
  }' | python3 -m json.tool
```

**Expected response:**
```json
{
  "trace_id": "trace-001",
  "span_id":  "span-001",
  "score": 1.0,
  "skipped": false,
  "skip_reason": null,
  "total_qualifying": 2,
  "entailed_count": 2,
  "sentence_results": [
    {"sentence": "The Eiffel Tower is in Paris.", "label": "entailment", "entailment_prob": 0.912},
    {"sentence": "It was built in 1889.", "label": "entailment", "entailment_prob": 0.887}
  ]
}
```

> **No model download needed** — DeBERTa is baked into the Docker image.

---

## Business Perspective

### What problem does this solve?

RAG-powered LLMs can hallucinate even when retrieved context is provided.
A response can be fluent, coherent, and well-formatted — yet factually contradict the source it was supposed to summarise.

**Faithfulness scoring detects this.** It answers one specific question per sentence:

> *"Is this claim supported by the context the model was given?"*

### Business Decision Flow

```
[Request arrives]
        |
        v
[FAITHFULNESS-ST-01 | Incoming call: response_text + rag_context + completion_tokens]
        |
        +-- [FAITHFULNESS-IN-01 | Input validation: null? too short? blocked?]
            |
            +-- [FAITHFULNESS-DC-01 | Should we score?]
                |
                |-- finish_reason = "content_filter"
                |   └── [SKIP] score=null, skip_reason=finish_reason_blocked
                |       └── Downstream: w_faith re-normalised to 0 (no penalty, no reward)
                |
                |-- rag_context is null
                |   └── [SKIP] score=null, skip_reason=rag_context_null
                |       └── Downstream: cannot grade what was never retrieved
                |
                |-- len(rag_context) < 50 chars
                |   └── [SKIP] score=null, skip_reason=rag_context_too_short
                |       └── Business rule: stub contexts carry no grounding signal
                |
                |-- completion_tokens < 10
                |   └── [SKIP] score=null, skip_reason=completion_tokens_too_few
                |       └── Business rule: refusals, one-word answers not scoreable
                |
                `-- All conditions pass
                    |
                    v
            [FAITHFULNESS-PR-01 | Split response into sentences (spaCy en_core_web_sm)]
                    |
                    +-- All sentences < 5 words
                    |   └── [SKIP] score=null, skip_reason=no_qualifying_sentences
                    |
                    `-- Qualifying sentences found
                        |
                        v
                [FAITHFULNESS-PR-02 | Is context > 512 words?]
                        |
                        |-- YES → split into ≤400-word chunks
                        |         for each sentence: NLI vs every chunk
                        |         take MAX entailment across chunks
                        |         (benefit-of-the-doubt: one supporting chunk is enough)
                        |
                        `-- NO  → NLI: batch all (context, sentence) pairs at once
                                |
                                v
                        [FAITHFULNESS-PR-03 | DeBERTa NLI · T=1.5 temperature scaling]
                                |
                                |  logits → scale by 1/T → softmax
                                |  → (P_entailment, P_neutral, P_contradiction)
                                |  → label = argmax
                                |
                                v
                        [FAITHFULNESS-PR-04 | Compute entailment fraction]
                                |
                                |  score = entailed_sentences / total_qualifying
                                |
                                v
                        [FAITHFULNESS-OUT-01 | Return score ∈ [0.0, 1.0]]
                                |
                                v
                        [FAITHFULNESS-CS-01 | Composite scorer uses w_faith=0.40]
                                |
                                |  composite = w_coh * coherence_score
                                |            + w_faith * faithfulness_score
                                |            + w_... * ...
                                |
                                |  if faithfulness_score IS NULL:
                                |    redistribute w_faith to remaining metrics
```

### Score Interpretation

| Score | Business meaning | Recommended action |
|---|---|---|
| `1.0` | Every claim grounded in context | ✅ Trusted response |
| `0.7–1.0` | Mostly grounded, minor gaps | ⚠️ Flag for review |
| `0.4–0.7` | Significant unsupported claims | 🔶 Warn user / log |
| `0.0–0.4` | Mostly hallucinated | 🚨 Alert / suppress |
| `null` | Not scoreable (skip condition) | ℹ️ Renormalize composite |

### Why Temperature Scaling (T=1.5)?

DeBERTa NLI models are over-confident — P(entailment)=0.97 for mildly supported claims.
T=1.5 softens the distribution before argmax, reducing false entailment labels
without retraining. This is calibration, not a business threshold.

---

## Architecture

```
[FastAPI port 8006]
      │
      ▼
score_faithfulness()  ← pure service, zero infra imports
      │
      ├── SentencizerPort ← SpacySentencizerAdapter (en_core_web_sm)
      └── NliScorerPort   ← DeBertaNliAdapter (cross-encoder/nli-deberta-v3-base)

Dependency arrows point INWARD. Domain never imports infra.
```

---

## Skip Conditions Reference

| `skip_reason` | Trigger | Business rationale |
|---|---|---|
| `finish_reason_blocked` | `finish_reason = "content_filter"` | Response was filtered; content may be incomplete |
| `rag_context_null` | `rag_context` is `null` | Nothing to ground against |
| `rag_context_too_short` | `len(rag_context) < 50 chars` | Stub/empty context — no signal |
| `completion_tokens_too_few` | `completion_tokens < 10` | Refusal, acknowledgement, or one-liner |
| `no_qualifying_sentences` | All sentences < 5 words after split | No scoreable claims |

---

## API Reference

### `POST /v1/score/faithfulness`

| Field | Type | Required | Notes |
|---|---|---|---|
| `trace_id` | string | ✅ | Upstream trace identifier |
| `span_id` | string | ✅ | Upstream span identifier |
| `rag_context` | string\|null | — | Retrieved context; null → skip |
| `response_text` | string | ✅ | LLM response to evaluate |
| `completion_tokens` | int | ✅ | < 10 → skip |
| `finish_reason` | string\|null | — | `"content_filter"` → skip |

**Response fields:**

| Field | Type | Notes |
|---|---|---|
| `score` | float\|null | `[0.0, 1.0]` or `null` if skipped |
| `skipped` | bool | True when any skip condition fires |
| `skip_reason` | string\|null | See skip table above |
| `total_qualifying` | int\|null | Sentence count after filtering |
| `entailed_count` | int\|null | Sentences labelled `entailment` |
| `sentence_results` | array | Per-sentence `{sentence, label, entailment_prob}` |

### `GET /health`

```json
{"status": "ok", "model_id": "cross-encoder/nli-deberta-v3-base"}
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NLI_MODEL_ID` | `cross-encoder/nli-deberta-v3-base` | HuggingFace model ID |
| `SPACY_MODEL` | `en_core_web_sm` | spaCy pipeline name |
| `DEPLOYMENT_ENV` | `dev` | Deployment environment (e.g., dev, production) |
| `SKIP_CONSOLE_EXPORTER` | `false` | Set to true to disable console span exporter |
| `SKIP_OTLP_EXPORTER` | `false` | Set to true to disable OTLP exporter |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP gRPC endpoint for trace collector |

---

## Observability & Tracing

The service is fully instrumented using OpenTelemetry. It propagates context from the incoming `trace_id` and `span_id` fields in the score request to downstream operations:
- `score_faithfulness`: Main parent span with attributes covering tokens, skipped status, and output.
- `sentencizer.split`: Sub-span tracking sentence count.
- `nli_scoring`: Sub-span tracking NLI model details, chunking, and batching.

By default, traces are exported to the Console Span Exporter and an OTLP collector endpoint.


---

## Local Development

```bash
# Install
pip install -e ".[dev]"
python -m spacy download en_core_web_sm

# Test
./scripts/test.sh

# Docker
docker-compose -f deploy/docker/docker-compose.yaml up
```

---

## CI/CD

- **Every push** to `packages/python/faithfulness/**` → runs 85 unit tests on Python 3.11 + 3.12
- **Merge to `main`** → tests must pass → builds and pushes `chiefj/faithfulness:latest`

Required GitHub Secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`

---

## Latency Budget (CPU)

| Step | ~Time |
|---|---|
| spaCy sentencize | 2ms |
| NLI per pair (CPU) | 48ms |
| 10 sentences, batch=8 | ~300ms |
| 10 sentences, long context (2 chunks) | ~550ms |

---

## Composite Score Weight

```
w_faith = 0.40  when score IS NOT NULL
w_faith = 0.00  when score IS NULL  →  redistribute to other metrics
```
