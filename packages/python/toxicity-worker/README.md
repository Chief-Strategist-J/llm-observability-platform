# Stateless Toxicity Worker

Production-ready multi-label toxicity classification worker service built with Hexagonal Architecture (Ports and Adapters) using `unitary/toxic-bert` run with ONNX Runtime on CPU.


## Installation and Dependencies

The service uses:
- `fastapi` & `uvicorn` for the REST API
- `optimum[onnxruntime]` for exporting and running the model on ONNX Runtime CPU
- `opentelemetry-api` & `opentelemetry-sdk` for tracing

## Configuration & Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | FastAPI service port | `8008` |
| `TOXICITY_MODEL_ID` | Model identifier or local path | `unitary/toxic-bert` |

---

## Docker Deployment

### Building the Image

```bash
docker build -t chiefj/toxicity-worker:latest -f build/Dockerfile .
```

### Running with Docker

Run the container by passing the environment variables:

```bash
docker run -d \
  -p 8008:8008 \
  -e PORT=8008 \
  -e TOXICITY_MODEL_ID=unitary/toxic-bert \
  --name toxicity-worker \
  chiefj/toxicity-worker:latest
```

---

## API Endpoint Contract

Defined in `contracts/openapi/v1.yaml`.

### POST /healthz / GET /healthz

Response:
```json
{
  "status": "ok",
  "model": "unitary/toxic-bert",
  "model_id": "unitary/toxic-bert"
}
```

### POST /score

Request:
```json
{
  "text": "response text here"
}
```

Response:
```json
{
  "toxicity": 0.02,
  "severe_toxicity": 0.00,
  "obscene": 0.01,
  "threat": 0.00,
  "insult": 0.02,
  "identity_hate": 0.00
}
```

For texts exceeding 510 tokens, the response will also include the long response strategy:
```json
{
  "toxicity": 0.02,
  "severe_toxicity": 0.00,
  "obscene": 0.01,
  "threat": 0.00,
  "insult": 0.02,
  "identity_hate": 0.00,
  "long_response_strategy": "max_of_two_passes"
}
```

## Running Tests

Run the test suite using pytest with the following command:

```bash
cd packages/python/toxicity-worker
python3 -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing
```
