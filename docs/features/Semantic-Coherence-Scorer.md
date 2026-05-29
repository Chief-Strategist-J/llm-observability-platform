# Semantic Coherence Scorer Service

The Semantic Coherence Scorer is a Layer 3 microservice designed to determine whether an LLM actually responded to the user's prompt (detecting off-topic generation). It works by computing the **cosine similarity** between the prompt embedding and response embedding.

Because the embeddings are pre-computed in Layer 1 (`queue-embedding-worker`), the Semantic Coherence Scorer performs zero additional vector calculations or LLM runs, avoiding extra model costs and keeping latency minimal.

---

## ⚡ 5-Minute Quickstart

### 1. Pull and Run the Image
The prebuilt image runs with the default `minilm` scorer:
```bash
docker pull chiefj/semantic-coherence:latest
docker run -d -p 8005:8005 --name semantic-coherence-scorer \
  -e EMBEDDING_WORKER_URL=http://localhost:8080 \
  chiefj/semantic-coherence:latest
```

### 2. Check Health
```bash
curl http://localhost:8005/health
```
**Response:**
```json
{
  "status": "ok",
  "scorers": ["minilm"]
}
```

### 3. Send a Scoring Request
```bash
curl -s -X POST http://localhost:8005/v1/score/semantic-coherence \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "trace-101",
    "span_id": "span-101",
    "prompt_type": "chat",
    "pii_detected": false,
    "prompt_embedding": [0.012, -0.054, 0.088],
    "response_embedding": [0.015, -0.052, 0.081]
  }' | python3 -m json.tool
```

---

## 🧠 Business Rules & Thresholds

The service categorizes similarity scores into `OK` or `LOW_COHERENCE` based on the query's classification:

| `prompt_type` | `LOW_COHERENCE` Threshold | Rationale |
|---|---|---|
| `chat` | $< 0.30$ | Chat/conversations tolerate minor drifts and general greetings. |
| `code` | $< 0.15$ | Code answers can use different variable names or commenting formats. |
| `rag` | $< 0.25$ | RAG responses must tightly bind to facts in the retrieved prompt context. |
| `classification` | $< 0.40$ | Labels and classifications must match the target classes. |

---

## 📋 Skip Conditions Reference

The pipeline skips calculating coherence in the following scenarios:

| Skip Reason | Trigger Condition | Rationale |
|---|---|---|
| `pii_detected` | `pii_detected` is `true` | Layer 1 skips embedding generation for safety when PII is present. |
| `prompt_embedding_null` | Prompt embedding is null in request and missing in DB | Cannot compute similarity without vectors. |
| `response_embedding_null` | Response embedding is null in request and missing in DB | Cannot compute similarity without vectors. |

---

## 📡 API Reference

### `GET /v1/scorers`
Lists all active models registered in the scorer registry and identifies which one is primary.
```json
{
  "scorers": [
    { "name": "minilm", "model_id": "sentence-transformers/all-MiniLM-L6-v2" }
  ],
  "primary": "minilm"
}
```

### `POST /v1/score/semantic-coherence`
**Request Schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `trace_id` | string | ✅ | Upstream trace identifier |
| `span_id` | string | ✅ | Upstream span identifier |
| `prompt_type` | string | ✅ | `chat` \| `code` \| `rag` \| `classification` |
| `pii_detected` | boolean | ✅ | Set to `true` if PII was flagged upstream |
| `prompt_embedding` | float[] | | Pre-computed prompt vector |
| `response_embedding` | float[] | | Pre-computed response vector |
| `scorers` | string[] | | Subset of scorers to run (omitting runs all) |
| `primary_scorer` | string | | Overrides the primary scorer name |

**Response Schema:**
```json
{
  "trace_id": "trace-101",
  "span_id": "span-101",
  "prompt_type": "chat",
  "skipped": false,
  "skip_reason": null,
  "primary": {
    "scorer_name": "minilm",
    "scorer_model": "sentence-transformers/all-MiniLM-L6-v2",
    "score": 0.94,
    "label": "OK",
    "skipped": false,
    "skip_reason": null
  },
  "all_scores": [
    {
      "scorer_name": "minilm",
      "scorer_model": "sentence-transformers/all-MiniLM-L6-v2",
      "score": 0.94,
      "label": "OK",
      "skipped": false,
      "skip_reason": null
    }
  ]
}
```

---

## 🎛️ Environment Variables & Scorer Hot-Swapping

The scorer architecture allows swapping or comparing similarity models with **zero code modifications** using runtime environment variables:

| Variable | Default | Description |
|---|---|---|
| `EMBEDDING_WORKER_URL` | `http://localhost:8080` | URL of the embedding worker (Layer 1) to fetch missing vectors. |
| `PRIMARY_SCORER` | `minilm` | Promotes this scorer's output to the `primary` field. |
| `SCORERS` | `minilm` | Comma-separated list of active scorers to load. |
| `SCORER_<NAME>_MODEL_ID` | (Built-in default) | Maps a custom Hugging Face model ID to the scorer name (e.g. `SCORER_MPNET_MODEL_ID=sentence-transformers/all-mpnet-base-v2`). |
