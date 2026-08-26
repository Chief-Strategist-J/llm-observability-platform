# Toxicity Service

Unified, production-ready multi-label toxicity classification service built on Hexagonal Architecture using `unitary/toxic-bert` with ONNX Runtime on CPU.

Merges the former `toxicity` (orchestrator) and `toxicity-worker` (stateless inference) packages into one. See [ADR 0003](./adr/0003-consolidation-of-toxicity-and-toxicity-worker.md).

---

## Key Features

| Feature | Detail |
|---|---|
| **ONNX CPU inference** | `unitary/toxic-bert` exported via `optimum` — no GPU required |
| **Dual-pass long-text** | Texts > 510 tokens scored in two passes; element-wise max taken across labels |
| **Optional Kafka publishing** | Flagged events (`score > 0.50`) emitted to `llm.toxicity.flagged` — disabled when `KAFKA_BOOTSTRAP_SERVERS` unset |
| **Model warmup** | Tokenizer + model loaded eagerly on startup via `lifespan()` — zero cold-start on first request |
| **Prometheus metrics** | Scraped at `/metrics` |
| **OTel tracing** | Every `/score` call wrapped in a span; upstream trace context linked via `traceparent` header or request body |

---

## Business Decision Tree

```
[Input: POST /score { text, trace_id?, span_id? }]
  │
  ├─ Tokenize text
  │
  ├─ Length > 510 tokens?
  │   ├─ YES → score(first 510) + score(last 510) → element-wise max
  │   │         long_response_strategy = "max_of_two_passes"
  │   └─ NO  → score(all tokens)
  │
  ├─ primary_score = scores.toxicity
  │
  ├─ primary_score > 0.50?
  │   ├─ YES → flagged=True, flag="TOXIC_RESPONSE"
  │   │         publish to Kafka llm.toxicity.flagged (if publisher wired)
  │   └─ NO  → flagged=False, flag=None
  │
  └─ Return ToxicityResult (scores + flagging + strategy)
```

---

## Module Structure

```
src/
├── core/domain/
│   ├── ports/
│   │   ├── toxicity_scorer_port.py     # Protocol: tokenize / score_token_ids
│   │   └── toxicity_publisher_port.py  # Protocol: publish_flagged
│   ├── rules.py                        # TOXICITY_THRESHOLD, is_flagged, determine_flag
│   ├── service.py                      # score_toxicity() — dual-pass + optional publish
│   └── types.py                        # ToxicityInput, ToxicityScores, ToxicityResult
├── infra/adapters/
│   ├── detoxify_onnx_adapter.py        # ONNX inference + warmup()
│   └── kafka_publisher_adapter.py      # confluent-kafka producer (no-op when unset)
├── api/rest/v1/
│   ├── app.py                          # FastAPI app: lifespan warmup + Prometheus + optional publisher
│   ├── router.py
│   └── handlers/
│       ├── health.py                   # GET/POST /healthz
│       └── score.py                    # POST /score
└── shared/tracing/tracer.py            # OTel TracerProvider init + trace_span() context manager
```

---

## Configuration & Environment Variables

| Variable | Description | Default |
|---|---|---|
| `TOXICITY_MODEL_ID` | HuggingFace model ID or local path | `unitary/toxic-bert` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers (comma-separated). When unset, publishing is disabled | `None` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint | `http://localhost:4317` |
| `SKIP_OTLP_EXPORTER` | Set `true` to disable OTLP exporter | `false` |
| `SKIP_CONSOLE_EXPORTER` | Set `true` to disable console span exporter | `false` |
| `DEPLOYMENT_ENV` | Environment tag on OTel resource | `dev` |

---

## API Contract

Full spec: [`contracts/openapi/v1.yaml`](./contracts/openapi/v1.yaml)

### `GET|POST /healthz`

```json
{ "status": "ok", "model_id": "unitary/toxic-bert" }
```

### `POST /score`

**Request:**
```json
{
  "text": "The response text to score",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7"
}
```
`trace_id` and `span_id` are optional. Upstream trace context is also accepted via the W3C `traceparent` header.

**Response:**
```json
{
  "toxicity": 0.08,
  "severe_toxicity": 0.001,
  "obscene": 0.002,
  "threat": 0.001,
  "insult": 0.003,
  "identity_hate": 0.001,
  "score": 0.08,
  "flagged": false,
  "skipped": false,
  "long_response_strategy": null
}
```

When `flagged: true`:
```json
{
  "toxicity": 0.87,
  "score": 0.87,
  "flagged": true,
  "flag": "TOXIC_RESPONSE",
  "skipped": false,
  "long_response_strategy": "max_of_two_passes"
}
```

> **Breaking change from v1**: the old `POST /v1/score/toxicity` endpoint with `response_text` field has been replaced by `POST /score` with `text` field (v0.2.0+).

---

## Docker Deployment

```bash
# Build
docker build -t chiefj/toxicity:latest -f build/Dockerfile .

# Run
docker run -d \
  -p 8008:8008 \
  -e TOXICITY_MODEL_ID=unitary/toxic-bert \
  -e KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:31418 \
  --name toxicity \
  chiefj/toxicity:latest
```

---

## Running Tests

```bash
cd packages/python/toxicity
SKIP_OTLP_EXPORTER=true SKIP_CONSOLE_EXPORTER=true \
  python3 -m pytest tests/ -v --tb=short
```

Skips `test_detoxify_onnx_adapter.py` in CI (requires torch + model download):

```bash
python3 -m pytest tests/ -v --ignore=tests/unit/test_detoxify_onnx_adapter.py
```

---

## Architecture Decision Records

See [`adr/`](./adr/README.md) for the full decision history.

| ADR | Decision |
|---|---|
| [0001](./adr/0001-onnx-cpu-inference-and-dual-pass-long-text-strategy.md) | ONNX Runtime CPU + dual-pass for texts > 510 tokens |
| [0002](./adr/0002-kafka-publisher-for-flagged-toxicity-events.md) | Kafka publishing of flagged events (optional) |
| [0003](./adr/0003-consolidation-of-toxicity-and-toxicity-worker.md) | Merge of `toxicity` + `toxicity-worker` into one package |
