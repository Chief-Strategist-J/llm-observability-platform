# NLI Worker

> **Layer 3 Stateless NLI Worker** — *A high-throughput, latency-optimized model service for grounding & faithfulness validation.*

This service runs the `cross-encoder/nli-deberta-v3-base` Natural Language Inference (NLI) model to perform sentence-pair classification. It serves as a stateless backend inference microservice (Model-as-a-Service) for evaluating the grounding of LLM completions against retrieved RAG context.

---

## Features

- **Stateless Inference**: Exposes lightweight REST endpoints powered by FastAPI and Uvicorn on port `8009`.
- **Eager Model Preloading**: Pre-caches and warms up tokenizer/model weights during container build and startup, eliminating cold-start latency.
- **Batched Execution**: Packages evaluations into configurable batches (default `8` pairs/pass, adjustable via `NLI_BATCH_SIZE`) for optimal GPU/CPU throughput.
- **Context Chunking**: Automatically splits context segments exceeding `400` tokens using the model tokenizer, performing a max-entailment aggregation across chunks.
- **Thread Safety**: Protects shared PyTorch resource states with thread locks to eliminate CUDA OOM errors under concurrent request traffic.
- **OpenTelemetry Instrumentation**: Integrates trace propagation using context headers for detailed profiling.

---

## API Documentation

### 1. Health Checks
**`GET/POST /healthz`**

**Response:**
```json
{
  "status": "ok",
  "model": "nli-deberta-v3-base",
  "device": "cpu"
}
```

### 2. NLI Grounding
**`POST /nli`**

**Request Body:**
```json
{
  "context": "The Eiffel Tower is located in Paris, France. It was built in 1889.",
  "sentences": [
    "The Eiffel Tower is in Paris.",
    "It was built in 2020."
  ],
  "temperature": 1.5
}
```

**Response:**
```json
{
  "results": [
    {
      "sentence": "The Eiffel Tower is in Paris.",
      "label": "entailment",
      "probabilities": {
        "entailment": 0.965,
        "neutral": 0.030,
        "contradiction": 0.005
      }
    },
    {
      "sentence": "It was built in 2020.",
      "label": "contradiction",
      "probabilities": {
        "entailment": 0.002,
        "neutral": 0.008,
        "contradiction": 0.990
      }
    }
  ],
  "faithfulness_score": 0.5,
  "flagged_sentences": [
    "It was built in 2020."
  ]
}
```

---

## Local Development

### 1. Create Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Run Tests
```bash
pytest tests/ -v
```

### 3. Run Server
```bash
uvicorn api.rest.v1.app:app --host 0.0.0.0 --port 8009
```
