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
