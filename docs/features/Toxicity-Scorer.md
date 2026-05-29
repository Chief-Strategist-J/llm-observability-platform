# Toxicity Scorer Service

The Toxicity Scorer is a production-ready, multi-label toxicity classification microservice designed to evaluate model responses. It is built using **Hexagonal Architecture (Ports and Adapters)**, using the `unitary/toxic-bert` model running on ONNX Runtime CPU for low latency and zero GPU dependencies.

---

## ⚡ 5-Minute Quickstart

### 1. Pull and Run the Image
The prebuilt Docker image is available on Docker Hub:
```bash
docker pull chiefj/toxicity:latest
docker run -d -p 8007:8007 --name toxicity-scorer chiefj/toxicity:latest
```

### 2. Check Health
Verify the service is alive and retrieve the active model:
```bash
curl http://localhost:8007/health
```
**Response:**
```json
{
  "status": "ok",
  "model_id": "unitary/toxic-bert"
}
```

### 3. Send a Scoring Request
```bash
curl -s -X POST http://localhost:8007/v1/score/toxicity \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "trace-999",
    "span_id": "span-999",
    "response_text": "This is a clean and polite response."
  }' | python3 -m json.tool
```

---

## 🧠 Dual-Pass Inference Strategy

Because standard BERT models are limited to a context window of 512 tokens, standard scorers truncate longer texts, potentially missing toxic content at the end of a long response.

To solve this, the Toxicity Scorer executes a **dual-pass evaluation** for texts exceeding 512 tokens:
1. **First Pass**: Evaluates the first 510 tokens.
2. **Second Pass**: Evaluates the last 510 tokens.
3. **Combination**: Combines the results of both passes by taking the **maximum score** across each classification label.

```
[Incoming Text > 512 tokens]
      │
      ├── Pass 1: First 510 tokens ──► [toxic-bert ONNX] ──► scores_first
      ├── Pass 2: Last 510 tokens  ──► [toxic-bert ONNX] ──► scores_last
      │
      └── Maximum Combination: max(scores_first, scores_last) ──► Final multi-label output
```

---

## 📋 Business Decision & Skip Rules

The toxicity classification uses a threshold to flag toxic responses.

*   **Toxicity Threshold**: `0.50`
*   **Flag Label**: `TOXIC_RESPONSE`

If a request fails due to an internal pipeline exception, the service does not fail the request; instead, it returns `skipped=true` with a `skip_reason="pipeline_failure"` to allow downstream systems to decide how to handle the error.

```
[Request Ingestion]
        │
        ▼
   Tokenization
        │
        ▼
  [ONNX Inference]
   (Dual-Pass if > 512 tokens)
        │
        ├── Exception ──► [Skip Result] score=null, skipped=true, skip_reason=pipeline_failure
        │
        ▼
   Primary Score
        │
        ├── Score > 0.50 ──► Flagged = true, Flag = "TOXIC_RESPONSE"
        │                    Emit to Kafka (llm.toxicity.flagged)
        │
        └── Score <= 0.50 ──► Flagged = false, Flag = null
```

---

## 📳 Kafka Publisher

When a response is flagged as toxic (`score > 0.50`), the service automatically publishes a message to the Kafka topic:

*   **Topic**: `llm.toxicity.flagged`
*   **Payload**:
    ```json
    {
      "trace_id": "trace-999",
      "span_id": "span-999",
      "score": 0.88,
      "scores": {
        "toxicity": 0.88,
        "severe_toxicity": 0.04,
        "obscene": 0.12,
        "threat": 0.01,
        "insult": 0.72,
        "identity_hate": 0.02
      }
    }
    ```

---

## 📡 API Reference

### `POST /v1/score/toxicity`

Scores the response text and checks for toxicity flags.

**Request Schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `trace_id` | string | ✅ | Trace identifier for tracing |
| `span_id` | string | ✅ | Span identifier for tracing |
| `response_text` | string | ✅ | Text content to evaluate |

**Response Schema:**

```json
{
  "trace_id": "trace-999",
  "span_id": "span-999",
  "score": 0.02,
  "flagged": false,
  "flag": null,
  "skipped": false,
  "skip_reason": null,
  "scores": {
    "toxicity": 0.02,
    "severe_toxicity": 0.001,
    "obscene": 0.002,
    "threat": 0.001,
    "insult": 0.003,
    "identity_hate": 0.001
  }
}
```

---

## 🛠️ Architecture and Ports

The service is decoupled from its infrastructure via Ports:
- `ToxicityScorerPort`: Decouples tokenization and model inference.
- `ToxicityPublisherPort`: Decouples event-streaming (Kafka) logic.

```
                  ┌──────────────────────┐
                  │   FastAPI (REST)     │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ score_toxicity()     │ (Domain Logic)
                  └─────┬──────────┬─────┘
                        │          │
         ┌──────────────┘          └──────────────┐
         ▼                                        ▼
   ToxicityScorerPort                       ToxicityPublisherPort
         ▲                                        ▲
         │ (Implements)                           │ (Implements)
   ┌─────┴──────────────┐                   ┌─────┴──────────────┐
   │ ONNXToxicityScorer │                   │ KafkaToxicityPub   │
   │ (ONNX Runtime CPU) │                   │ (confluent-kafka)  │
   └────────────────────┘                   └────────────────────┘
```

---

## 📊 Observability

The service propagates trace contexts and registers the following spans:
- `score_toxicity`: Parent span with attributes `input.text_length`, `output.score`, `output.flagged`, and `skipped`.
- `toxicity.tokenize`: Sub-span tracking sentence-to-tokens conversion latency and token counts.
- `model_inference`: Sub-span measuring raw ONNX Runtime inference latency.
