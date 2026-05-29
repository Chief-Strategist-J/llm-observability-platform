# REST Management API

Full reference for all HTTP endpoints exposed by the observability container. By default, the API is served at `http://localhost:8002/v1`.

---

## Endpoint Feature Map

```
FastAPI REST API (localhost:8002)
│
├── /spans
│   └── POST /             → Ingest/report manual telemetry span
│
├── /instrumentation
│   ├── POST /init         → Enable monkey-patching
│   ├── POST /uninstrument → Remove active patches
│   ├── POST /detect       → Discover provider/model
│   └── POST /test-call    → Verify trace output
│
├── /fallback
│   ├── POST /track        → Track fallback model retry attempt
│   └── POST /clear        → Reset active fallback registry cache
│
├── /tool-call
│   ├── POST /track        → Track trace-accumulated tool-call costs
│   └── POST /clear        → Reset active tool-call registry cache
│
├── /token-counting
│   └── POST /count        → Local token evaluation
│
├── /streaming
│   └── POST /test-stream-call → Server-Sent Events test
│
├── /pii-injection
│   └── POST /scan         → Aho-Corasick & regex match
│
├── /sampling
│   └── POST /should-sample → Evaluate modulo gate
│
├── /embeddings
│   └── POST /embed        → Vector conversion
│
└── /metrics
    ├── POST /init         → Start scrape endpoint
    ├── GET  /health       → Check metrics status
    ├── POST /record       → Log single span metrics
    ├── POST /record-batch → Log bulk spans metrics
    ├── GET  /prices       → Retrieve current model prices
    └── POST /prices/reload → Reload pricing configurations
```

---

## 1. Span Ingestion

### `POST /spans`
Ingest manual LLM telemetry spans directly into the local WAL reporter.

*   **Request Body**:
    ```json
    {
      "trace_id": "trace-888",
      "span_id": "span-888",
      "model": "gpt-4o",
      "provider": "openai",
      "service_name": "recommender",
      "prompt_tokens": 150,
      "completion_tokens": 50,
      "cost_usd_micro": 1500,
      "latency_ms_total": 420,
      "latency_ms_ttft": 80,
      "finish_reason": "stop",
      "status": "success",
      "retry_count": 0,
      "pii_detected": false,
      "injection_attempt": false
    }
    ```

*   **Response (202 Accepted)**:
    ```json
    {
      "success": true,
      "span_warnings": []
    }
    ```

*   **Response (400 Bad Request - Validation Error)**:
    ```json
    {
      "error": "Validation failed for field 'prompt_tokens': Input should be greater than 0",
      "rule": "RULE-V-02"
    }
    ```

---

## 2. Instrumentation Management

### `POST /instrumentation/init`
Enable auto-instrumentation globally in the application runtime.
- **Request Body**: None
- **Response** (`application/json`):
  ```json
  {"success": true, "message": "Auto-instrumentation initialized"}
  ```

---

### `POST /instrumentation/uninstrument`
Remove all active auto-instrumentation monkey-patches.
- **Request Body**: None
- **Response** (`application/json`):
  ```json
  {"success": true, "message": "All instrumentation disabled"}
  ```

---

### `POST /instrumentation/detect`
Parse a sample request body to discover the provider name and model.
- **Request Body**:
  ```json
  {
    "url": "https://api.openai.com/v1/chat/completions",
    "body": "{\"model\": \"gpt-4o\"}"
  }
  ```
- **Response**:
  ```json
  {"provider": "openai", "model": "gpt-4o"}
  ```

---

### `POST /instrumentation/test-call`
Trigger an outbound call to verify metrics and tracing flow.
- **Request Body**:
  ```json
  {
    "method": "httpx",
    "provider": "openai"
  }
  ```
  *Allowed `method` values: `httpx`, `requests`, `sdk`. Allowed `provider` values: `openai`, `anthropic`.*
- **Response**:
  ```json
  {"success": true, "message": "Test call triggered via httpx for openai"}
  ```

---

## 3. Fallback Tracking

### `POST /fallback/track`
Tracks fallback model attempts for a given request trace.
- **Request Body**:
  ```json
  {
    "trace_id": "trace-777",
    "model": "claude-3-opus"
  }
  ```
- **Response**:
  ```json
  {
    "retry_count": 2,
    "attempted_models": ["gpt-4o", "claude-3-opus"]
  }
  ```

---

### `POST /fallback/clear`
Clears the active fallback tracking cache.
- **Request Body**: None
- **Response**:
  ```json
  {
    "success": true
  }
  ```

---

## 4. Tool Call Tracking

### `POST /tool-call/track`
Tracks trace-accumulated costs across nested tool invocations.
- **Request Body**:
  ```json
  {
    "trace_id": "trace-888",
    "span_id": "span-888",
    "cost": 150
  }
  ```
- **Response**:
  ```json
  {
    "total_cost": 450
  }
  ```

---

### `POST /tool-call/clear`
Clears the active tool-call cost tracking cache.
- **Request Body**: None
- **Response**:
  ```json
  {
    "success": true
  }
  ```

---

## 5. Utility Engine

### `POST /token-counting/count`
Count prompt tokens locally without contacting the LLM provider.
- **Request Body** (Plain String):
  ```json
  {
    "prompt": "Hello, how are you?",
    "model": "gpt-4o"
  }
  ```
- **Request Body** (Chat Messages):
  ```json
  {
    "prompt": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Summarize this document."}
    ],
    "model": "gpt-4o"
  }
  ```
- **Response**:
  ```json
  {"tokens": 20, "method": "tiktoken"}
  ```

---

### `POST /pii-injection/scan`
Scan inputs for PII and injection exploits.
- **Request Body**:
  ```json
  {"prompt": "My email is test@example.com and DROP TABLE users;"}
  ```
- **Response**:
  ```json
  {
    "pii_detected": true,
    "injection_attempt": true
  }
  ```

---

### `POST /embeddings/embed`
Convert text into a 384-dimensional MiniLM-L6-v2 vector embedding.
- **Request Body**:
  ```json
  {"text": "Explain transformers."}
  ```
- **Response**:
  ```json
  {
    "embedding": [0.021, -0.103, 0.044, "...381 more floats..."]
  }
  ```

---

### `POST /sampling/should-sample`
Check if a span ID passes the 1% deterministic modulo-100 gate.
- **Request Body**:
  ```json
  {"span_id": "550e8400-e29b-41d4-a716-446655440000"}
  ```
- **Response**:
  ```json
  {"is_sampled": false}
  ```

---

## 6. Prometheus Metrics & Records

### `POST /metrics/init`
Initialize the local Prometheus scraper endpoint.
- **Request Body**:
  ```json
  {"port": 9464}
  ```
- **Response**:
  ```json
  {"initialized": true, "message": "Metrics pipeline initialized"}
  ```

---

### `GET /metrics/health`
Check if the Prometheus metrics pipeline is initialized and active.
- **Request Body**: None
- **Response**:
  ```json
  {
    "initialized": true,
    "message": "Metrics pipeline is active"
  }
  ```

---

### `POST /metrics/record`
Record variables for a single span to generate metrics and compute USD pricing.
- **Request Body**:
  ```json
  {
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
  }
  ```
- **Response**:
  ```json
  {
    "recorded": true,
    "cost_usd_micro": 1500,
    "price_version": "2025-01-15"
  }
  ```

---

### `POST /metrics/record-batch`
Record variables for multiple spans in a single bulk operation.
- **Request Body**:
  ```json
  {
    "spans": [
      {
        "model": "gpt-4o",
        "provider": "openai",
        "prompt_tokens": 100,
        "completion_tokens": 50
      }
    ]
  }
  ```
- **Response**:
  ```json
  {
    "recorded_count": 1
  }
  ```

---

### `GET /metrics/prices`
Retrieves the currently loaded pricing configurations.
- **Request Body**: None
- **Response**:
  ```json
  {
    "prices": [
      {
        "model": "gpt-4o",
        "provider": "openai",
        "input_price_per_1m": 2.50,
        "output_price_per_1m": 10.00,
        "version": "2025-01-15"
      }
    ]
  }
  ```

---

### `POST /metrics/prices/reload`
Reloads the pricing configuration from the local `model_prices.yaml` file dynamically.
- **Request Body**: None
- **Response**:
  ```json
  {
    "initialized": true,
    "message": "Model prices reloaded successfully"
  }
  ```

---

## Next Steps

- [Docker & CLI Deployment](Docker-and-CLI-Deployment.md) - Run and expose the API container.
- [Config Files Reference](Config-Files-Reference.md) - Learn how prices and regex patterns are configured.

