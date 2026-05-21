# REST Management API

Full reference for all API endpoints. Base URL: `http://localhost:8002/v1`

---

## Instrumentation Management

### `POST /instrumentation/init`

Enable auto-instrumentation remotely.

```bash
curl -X POST http://localhost:8002/v1/instrumentation/init
```
```json
{"success": true, "message": "Auto-instrumentation initialized"}
```

---

### `POST /instrumentation/uninstrument`

Disable all active instrumentation patches.

```bash
curl -X POST http://localhost:8002/v1/instrumentation/uninstrument
```
```json
{"success": true, "message": "All instrumentation disabled"}
```

---

### `POST /instrumentation/detect`

Detect provider and model from a sample request body. Useful for discovery before initializing.

```bash
curl -X POST http://localhost:8002/v1/instrumentation/detect \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.openai.com/v1/chat/completions",
    "body": "{\"model\": \"gpt-4o\"}"
  }'
```
```json
{"provider": "openai", "model": "gpt-4o"}
```

```bash
# Anthropic
curl -X POST http://localhost:8002/v1/instrumentation/detect \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.anthropic.com/v1/messages",
    "body": "{\"model\": \"claude-3-5-sonnet\"}"
  }'
```
```json
{"provider": "anthropic", "model": "claude-3-5-sonnet"}
```

---

### `POST /instrumentation/test-call`

Trigger a real outbound test call to verify end-to-end tracing.

```bash
curl -X POST http://localhost:8002/v1/instrumentation/test-call \
  -H "Content-Type: application/json" \
  -d '{"method": "httpx", "provider": "openai"}'
```

`method` options: `httpx`, `requests`, `sdk`
`provider` options: `openai`, `anthropic`

```json
{"success": true, "message": "Test call triggered via httpx for openai"}
```

---

## Token Counting

### `POST /token-counting/count`

Count prompt tokens before sending to the LLM.

```bash
# Plain string
curl -X POST http://localhost:8002/v1/token-counting/count \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you?", "model": "gpt-4o"}'
```
```json
{"tokens": 6, "method": "tiktoken"}
```

```bash
# Chat message list
curl -X POST http://localhost:8002/v1/token-counting/count \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Summarize this document."}
    ],
    "model": "gpt-4o"
  }'
```
```json
{"tokens": 20, "method": "tiktoken"}
```

`method` will be `tiktoken` for known models, `estimated` for unknown ones.

---

## Streaming

### `POST /streaming/test-stream-call`

Trigger a mock streaming call and receive SSE chunks.

```bash
curl -X POST http://localhost:8002/v1/streaming/test-stream-call \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "chunks": ["The", " answer", " is", " 42"]}'
```

Response (`text/event-stream`):
```
data: The

data:  answer

data:  is

data:  42
```

---

## PII & Injection Scanning

### `POST /pii-injection/scan`

Scan a prompt string or message list.

```bash
curl -X POST http://localhost:8002/v1/pii-injection/scan \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Call me at 555-867-5309"}'
```
```json
{"pii_detected": false, "injection_attempt": false}
```

```bash
curl -X POST http://localhost:8002/v1/pii-injection/scan \
  -H "Content-Type: application/json" \
  -d '{"prompt": "My SSN is 123-45-6789 and DROP TABLE users"}'
```
```json
{"pii_detected": true, "injection_attempt": true}
```

---

## Deterministic Sampling

### `POST /sampling/should-sample`

Check whether a span ID passes the 1% sampling gate.

```bash
curl -X POST http://localhost:8002/v1/sampling/should-sample \
  -H "Content-Type: application/json" \
  -d '{"span_id": "550e8400-e29b-41d4-a716-446655440000"}'
```
```json
{"is_sampled": false}
```

---

## MiniLM Embeddings

### `POST /embeddings/embed`

Generate a 384-dimensional embedding for a text string.

```bash
curl -X POST http://localhost:8002/v1/embeddings/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "Explain the attention mechanism in transformers."}'
```
```json
{
  "embedding": [0.021, -0.103, 0.044, 0.189, "...380 more values..."]
}
```

---

## Metrics

### `POST /metrics/init`

Initialize the Prometheus metrics scrape pipeline.

```bash
curl -X POST http://localhost:8002/v1/metrics/init \
  -H "Content-Type: application/json" \
  -d '{"port": 9464}'
```
```json
{"initialized": true, "message": "Metrics pipeline initialized"}
```

---

### `GET /metrics/health`

```bash
curl http://localhost:8002/v1/metrics/health
```
```json
{"initialized": true, "message": "Metrics pipeline is active"}
```

---

### `POST /metrics/record`

Record metrics for a single span.

```bash
curl -X POST http://localhost:8002/v1/metrics/record \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "provider": "openai",
    "service_name": "chat-api",
    "prompt_tokens": 120,
    "completion_tokens": 60,
    "latency_ms_total": 380,
    "latency_ms_ttft": 90,
    "finish_reason": "stop",
    "status": "success",
    "pii_detected": false,
    "injection_attempt": false,
    "retry_count": 0
  }'
```
```json
{"recorded": true, "cost_usd_micro": 1500, "price_version": "2025-01-15"}
```

---

### `POST /metrics/record-batch`

Record metrics for multiple spans in one call.

```bash
curl -X POST http://localhost:8002/v1/metrics/record-batch \
  -H "Content-Type: application/json" \
  -d '{
    "spans": [
      {"model": "gpt-4o", "provider": "openai", "service_name": "svc-a",
       "prompt_tokens": 100, "completion_tokens": 50, "latency_ms_total": 300, "status": "success"},
      {"model": "gpt-3.5-turbo", "provider": "openai", "service_name": "svc-b",
       "prompt_tokens": 800, "completion_tokens": 200, "latency_ms_total": 900, "status": "success"}
    ]
  }'
```
```json
{"recorded_count": 2}
```

---

## All Endpoints at a Glance

| Method | Path | Feature |
|---|---|---|
| `POST` | `/instrumentation/init` | Enable auto-instrumentation |
| `POST` | `/instrumentation/uninstrument` | Disable all patches |
| `POST` | `/instrumentation/detect` | Provider/model discovery |
| `POST` | `/instrumentation/test-call` | End-to-end trace verification |
| `POST` | `/streaming/test-stream-call` | Streaming + TTFT verification |
| `POST` | `/token-counting/count` | Token count (string or message list) |
| `POST` | `/pii-injection/scan` | PII and injection detection |
| `POST` | `/sampling/should-sample` | Sampling gate check |
| `POST` | `/embeddings/embed` | 384-dim MiniLM embedding |
| `POST` | `/metrics/init` | Initialize Prometheus pipeline |
| `GET`  | `/metrics/health` | Metrics pipeline health |
| `POST` | `/metrics/record` | Record single span metrics |
| `POST` | `/metrics/record-batch` | Record batch span metrics |

---

## Next: [Docker & CLI Deployment](Docker-and-CLI-Deployment)
