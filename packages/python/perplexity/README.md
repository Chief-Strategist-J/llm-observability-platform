# Perplexity Scorer

> Layer 3 perplexity scoring microservice — **Score 4** in the LLM Observability composite quality index.
> Runs on port **8007**. Zero GPU required.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Run Locally (Python)](#run-locally-python)
3. [Run with Docker](#run-with-docker)
4. [Run with Docker Compose](#run-with-docker-compose)
5. [API Reference](#api-reference)
6. [Skip Conditions](#skip-conditions)
7. [Baselines & Alerting](#baselines--alerting)
8. [Composite Weight](#composite-weight)
9. [Environment Variables](#environment-variables)
10. [CI / CD](#ci--cd)
11. [Algorithm](#algorithm)

---

## What It Does

Scores the cross-entropy perplexity of an LLM response.

| Scorer path | When used | Cost |
|---|---|---|
| **Provider logprobs** (primary) | `token_logprobs` array provided | Zero inference |
| **GPT-2 124M ONNX** (fallback) | No logprobs supplied | ~25ms on CPU |

Returns `null` (skipped) when skip conditions are met. The composite weight drops to `0.00` automatically.

---

## Run Locally (Python)

```bash
cd packages/python/perplexity

pip install -e ".[dev]"

SKIP_CONSOLE_EXPORTER=true SKIP_OTLP_EXPORTER=true \
  pytest tests/ --cov=src -v
```

Start the server:

```bash
PYTHONPATH=src uvicorn api.rest.v1.app:app --host 0.0.0.0 --port 8007 --reload
```

---

## Run with Docker

### Pull and run the published image

```bash
docker pull chiefj/perplexity:latest

docker run -d \
  --name perplexity \
  -p 8007:8007 \
  -e SKIP_OTLP_EXPORTER=true \
  chiefj/perplexity:latest
```

### Health check

```bash
curl http://localhost:8007/health
# {"status":"ok","scorer":"provider_logprobs"}
```

### Score a response (with provider logprobs)

```bash
curl -X POST http://localhost:8007/v1/score/perplexity \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "abc123",
    "span_id": "def456",
    "response_text": "The mitochondria is the powerhouse of the cell.",
    "completion_tokens": 12,
    "prompt_type": "chat",
    "token_logprobs": [-1.2, -0.9, -1.5, -2.1, -0.8, -1.3, -1.0, -0.7, -1.4, -2.0, -1.1, -0.6]
  }'
```

Expected response:

```json
{
  "trace_id": "abc123",
  "span_id": "def456",
  "perplexity": 3.31,
  "score": 0.72,
  "weight": 0.10,
  "skipped": false,
  "skip_reason": null,
  "high_perplexity_flag": false,
  "prompt_type": "chat",
  "scorer_used": "provider_logprobs"
}
```

### Score a response (GPT-2 fallback — no logprobs)

```bash
curl -X POST http://localhost:8007/v1/score/perplexity \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "xyz789",
    "span_id": "qrs012",
    "response_text": "Paris is the capital of France and a major European city.",
    "completion_tokens": 15,
    "prompt_type": "rag"
  }'
```

### Skipped response (too few tokens)

```bash
curl -X POST http://localhost:8007/v1/score/perplexity \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "skip1",
    "span_id": "skip2",
    "response_text": "Yes.",
    "completion_tokens": 2,
    "prompt_type": "chat"
  }'
# {"skipped": true, "skip_reason": "completion_tokens_too_few", "weight": 0.0, ...}
```

### Build the image locally

```bash
cd packages/python/perplexity

docker build \
  -f build/Dockerfile \
  -t chiefj/perplexity:local \
  .
```

---

## Run with Docker Compose

```bash
cd packages/python/perplexity

docker compose -f deploy/docker/docker-compose.yaml up -d
```

Stop:

```bash
docker compose -f deploy/docker/docker-compose.yaml down
```

---

## API Reference

Full contract: [`contracts/openapi/v1.yaml`](contracts/openapi/v1.yaml)

### `POST /v1/score/perplexity`

| Field | Type | Required | Description |
|---|---|---|---|
| `trace_id` | string | ✅ | Distributed trace ID |
| `span_id` | string | ✅ | Parent span ID |
| `response_text` | string | ✅ | LLM completion text |
| `completion_tokens` | int | ✅ | Token count — `< 10` triggers skip |
| `prompt_type` | enum | ✅ | `chat` \| `code` \| `rag` \| `classification` |
| `token_logprobs` | float[] | ❌ | Provider log-probs (primary path) |
| `finish_reason` | string | ❌ | `content_filter` triggers skip |

### `POST /perplexity`

Dual-path perplexity scoring for HTTP inference.

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | ✅ | The text to score |
| `logprobs` | float[][] | ❌ | Optional nested or candidate provider logprob array |

Returns:
```json
{
  "perplexity": 18.4,
  "method": "provider_logprobs" | "gpt2_onnx",
  "token_count": 187
}
```

### `GET /health`

Returns `{"status": "ok", "scorer": "<provider_logprobs|gpt2_onnx|unavailable>"}`.

---

## Skip Conditions

| Condition | `skip_reason` | `weight` |
|---|---|---|
| `completion_tokens < 10` | `completion_tokens_too_few` | 0.00 |
| `finish_reason == "content_filter"` | `finish_reason_blocked` | 0.00 |
| No logprobs AND GPT-2 unavailable | `scorer_unavailable` | 0.00 |

---

## Baselines & Alerting

| `prompt_type` | Expected perplexity | HIGH flag threshold (`3 ×`) |
|---|---|---|
| `chat` | 15–35 | > 105 |
| `code` | 8–20 | > 60 |
| `rag` | 12–28 | > 84 |
| `classification` | 6–15 | > 45 |

`high_perplexity_flag: true` indicates the model was likely confused, hallucinating, or output low-quality text.

---

## Composite Weight

| State | `w_perplexity` | `score` contribution |
|---|---|---|
| perplexity available | **0.10** | `1/log(perplexity)` → normalized to [0, 1] |
| perplexity skipped | **0.00** | other scorer weights renormalized externally |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GPT2_MODEL_PATH` | `gpt2` | HuggingFace model ID or local path for GPT-2 ONNX |
| `SKIP_CONSOLE_EXPORTER` | `false` | Suppress OTel console span output |
| `SKIP_OTLP_EXPORTER` | `true` | Disable OTLP gRPC/HTTP exporter |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP collector endpoint |
| `DEPLOYMENT_ENV` | `dev` | OTel resource `deployment.env` attribute |

Copy `.env.example` to `.env` to configure locally.

---

## CI / CD

The pipeline (`perplexity-ci.yml`) triggers **only** when files under `packages/python/perplexity/` change and the target branch is `main`:

| Event | Jobs triggered |
|---|---|
| Pull request → `main` (perplexity path) | `test` (Python 3.11 + 3.12) |
| Push/merge → `main` (perplexity path) | `test` (Python 3.11 + 3.12) |

Docker builds and pushes are done **manually** via the deploy script — not in CI.

---

## Algorithm

```
Primary path (provider logprobs):
  perplexity = exp( -1/N × Σ token_logprobs )

Fallback path (GPT-2 124M ONNX, CPU):
  perplexity = exp( cross_entropy_loss )   # ~25ms / 200 tokens

Normalized score:
  contribution = 1 / log(perplexity)
  score        = clamp((contribution - low) / (high - low), 0, 1)
```
