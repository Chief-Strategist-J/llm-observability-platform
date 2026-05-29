# Toxicity Scorer Service

Production-ready multi-label toxicity classification service built with Hexagonal Architecture (Ports and Adapters) using `unitary/toxic-bert` run with ONNX Runtime on CPU.

## Key Features

1. **Dual-Pass Inference Strategy**:
   - For long response texts exceeding 512 tokens, the service executes a dual-pass evaluation (evaluating the first 512 tokens and the last 512 tokens separately).
   - Combines the scores by taking the maximum score across each label to ensure toxicity at the end of a long response is flagged.
2. **Hexagonal Architecture**:
   - Zero infrastructure dependencies inside the domain logic.
   - External dependencies are decoupled via `ToxicityScorerPort` and `ToxicityPublisherPort` protocols.
3. **Observability**:
   - Fully instrumented with OpenTelemetry tracing spans.
   - Propagates trace/span context through headers and publishes flags.
4. **Kafka Publisher**:
   - Emits flagged toxic responses (`toxicity_score > 0.50`) to the `llm.toxicity.flagged` Kafka topic.

## Business Decision Tree

```
[toxicity-ST-01 | Input Text Received]
   |
   +-- [toxicity-IN-01 | response_text (str)]
       |
       +-- [toxicity-PR-01 | Tokenizer evaluation: Check length in tokens]
           |
           +-- [toxicity-DC-01 | Length > 512 tokens?]
               |-- [yes | Dual-Pass Inference: Pass 1 (first 512 tokens) AND Pass 2 (last 512 tokens)]
               |          Combination: toxicity_score = max(score_first, score_last)
               |-- [no  | Single-Pass Inference: Pass 1 (first 512 tokens)]
               |
               `-- [toxicity-PR-02 | Threshold check: primary score = output['toxicity']]
                   |
                   +-- [toxicity-DC-02 | primary score > 0.50?]
                       |-- [yes | Flag: 'TOXIC_RESPONSE']
                       |          Action: Emit event to Kafka topic 'llm.toxicity.flagged'
                       |-- [no  | Flag: None]
                       |          Action: Do not emit Kafka event
                       |
                       `-- [toxicity-OUT-01 | Return ToxicityResult](data / response / event / update / artifact)
                           |   
                           |
                           `-- [toxicity-CS-01 | Toxicity scored, tracing context populated]
```

## Registry Integration

- Registered on Port **8007**.
- Feature configuration registered in `registry/features/toxicity.yaml`.
- Worker service registered in `registry/workers/toxicity.yaml`.

## Installation and Dependencies

The service uses:
- `fastapi` & `uvicorn` for the REST API
- `optimum[onnxruntime]` for exporting and running the model on ONNX Runtime CPU
- `confluent-kafka` for optional event publishing
- `opentelemetry-api` & `opentelemetry-sdk` for tracing

## Configuration & Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | FastAPI service port | `8007` |
| `TOXICITY_MODEL_ID` | Model identifier or local path | `unitary/toxic-bert` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers list (comma-separated) | `None` (disables publishing) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry collector endpoint | `None` |
| `SKIP_OTLP_EXPORTER` | Skip OTLP exporter initialization | `false` |
| `SKIP_CONSOLE_EXPORTER` | Skip logging spans to console stdout | `true` |

---

## Docker Deployment

### Building the Image

```bash
docker build -t chiefj/toxicity:latest -f build/Dockerfile .
```

### Running with Docker

Run the container by passing the environment variables:

```bash
docker run -d \
  -p 8007:8007 \
  -e PORT=8007 \
  -e TOXICITY_MODEL_ID=unitary/toxic-bert \
  -e KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces \
  -e SKIP_OTLP_EXPORTER=false \
  -e SKIP_CONSOLE_EXPORTER=true \
  --name toxicity-service \
  chiefj/toxicity:latest
```

---

## API Endpoint Contract

Defined in `contracts/openapi/v1.yaml`.

### POST /v1/score/toxicity

Request:
```json
{
  "trace_id": "string",
  "span_id": "string",
  "response_text": "string"
}
```

Response:
```json
{
  "trace_id": "string",
  "span_id": "string",
  "score": 0.08,
  "flagged": false,
  "flag": null,
  "skipped": false,
  "skip_reason": null,
  "scores": {
    "toxicity": 0.08,
    "severe_toxicity": 0.001,
    "obscene": 0.002,
    "threat": 0.001,
    "insult": 0.003,
    "identity_hate": 0.001
  }
}
```

## Running Tests

Run the test suite using pytest with the following command:

```bash
cd packages/python/toxicity
PYTHONPATH=src python3 -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing
```
