# Faithfulness Scorer Service

The Faithfulness Scorer is a Layer 3 microservice designed to detect hallucinations in RAG (Retrieval-Augmented Generation) pipelines. It evaluates the factual grounding of an LLM response against the retrieved source documents, outputting an entailment fraction based on the `cross-encoder/nli-deberta-v3-base` model.

---

## ⚡ 5-Minute Quickstart

### 1. Pull and Run the Image
The prebuilt image comes with the DeBERTa model baked in for out-of-the-box CPU inference:
```bash
docker pull chiefj/faithfulness:latest
docker run -d -p 8006:8006 --name faithfulness-scorer chiefj/faithfulness:latest
```

### 2. Check Health
```bash
curl http://localhost:8006/health
```
**Response:**
```json
{"status": "ok", "model_id": "cross-encoder/nli-deberta-v3-base"}
```

### 3. Send a Scoring Request
```bash
curl -s -X POST http://localhost:8006/v1/score/faithfulness \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "trace-001",
    "span_id":  "span-001",
    "rag_context": "The Eiffel Tower is located in Paris, France. It was built in 1889 by Gustave Eiffel.",
    "response_text": "The Eiffel Tower is in Paris. It was built in 1889.",
    "completion_tokens": 14
  }' | python3 -m json.tool
```

---

## 🧠 Entailment Calculation Logic

The service implements Natural Language Inference (NLI) to analyze the factual alignment between each sentence in the response and the provided RAG context:

1.  **Sentence Splitting**: The LLM response is split into individual sentences using `spaCy` (`en_core_web_sm`).
2.  **Length Filtering**: Only sentences containing **5 or more words** qualify for scoring. Short stubs, greetings, or acknowledgements are excluded.
3.  **Context Chunking**: If the RAG context exceeds 512 words, it is split into overlapping chunks of $\le 400$ words. Each sentence is evaluated against all chunks, and the **maximum entailment score** is recorded (benefit-of-the-doubt rule: if any part of the context supports the claim, it is considered grounded).
4.  **DeBERTa NLI Inference**: The service feeds `(context_chunk, sentence)` pairs to the NLI cross-encoder model.
5.  **Temperature Scaling (T = 1.5)**: DeBERTa models tend to be over-confident. The service divides logits by `1.5` before running softmax to calibrate the probability distribution (`P_entailment`, `P_neutral`, `P_contradiction`).
6.  **Label Mapping**: The label with the highest calibrated probability is assigned (`entailment`, `neutral`, or `contradiction`).
7.  **Entailment Fraction**: The final score is:
    $$\text{score} = \frac{\text{count(entailed\_sentences)}}{\text{count(qualifying\_sentences)}}$$

---

## 📋 Skip Conditions Reference

To avoid generating skewed or incorrect scores, the pipeline automatically skips evaluation when specific criteria are met:

| Skip Reason | Trigger Condition | Rationale |
|---|---|---|
| `finish_reason_blocked` | `finish_reason = "content_filter"` | The generation was terminated prematurely due to safety filters. |
| `rag_context_null` | `rag_context` is `null` or empty | Grounding is impossible without source documents. |
| `rag_context_too_short` | `len(rag_context) < 50` characters | The context is likely a placeholder or failure message. |
| `completion_tokens_too_few` | `completion_tokens < 10` | Short responses (e.g., "Yes", "I don't know") do not contain testable claims. |
| `no_qualifying_sentences` | All split sentences are $< 5$ words long | No sentence has enough semantic weight to check. |

---

## 📡 API Reference

### `POST /v1/score/faithfulness`

Scores a RAG response text against the retrieved context.

**Request Schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `trace_id` | string | ✅ | Upstream trace identifier |
| `span_id` | string | ✅ | Upstream span identifier |
| `response_text` | string | ✅ | LLM response to evaluate |
| `completion_tokens` | integer | ✅ | Token count of the response (checks for minimal length) |
| `rag_context` | string | | Retrieved context documents |
| `finish_reason` | string | | Finish reason of the LLM call |

**Response Schema:**

```json
{
  "trace_id": "trace-001",
  "span_id": "span-001",
  "score": 1.0,
  "skipped": false,
  "skip_reason": null,
  "total_qualifying": 2,
  "entailed_count": 2,
  "sentence_results": [
    {
      "sentence": "The Eiffel Tower is in Paris.",
      "label": "entailment",
      "entailment_prob": 0.912
    },
    {
      "sentence": "It was built in 1889.",
      "label": "entailment",
      "entailment_prob": 0.887
    }
  ]
}
```

---

## 🎛️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NLI_MODEL_ID` | `cross-encoder/nli-deberta-v3-base` | Hugging Face model repository ID. |
| `SPACY_MODEL` | `en_core_web_sm` | spaCy model used for sentence tokenization. |
| `DEPLOYMENT_ENV` | `dev` | Service environment name. |
| `SKIP_CONSOLE_EXPORTER` | `false` | Set to `true` to disable tracing console output. |
| `SKIP_OTLP_EXPORTER` | `false` | Set to `true` to disable OTLP gRPC exports. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | Endpoint for the Tempo/OTel collector. |

---

## 📊 Tracing & Telemetry Spans

The service integrates standard OpenTelemetry tracing context propagation from incoming requests:
- `score_faithfulness`: Parent span capturing length attributes, token counts, and final scores.
- `sentencizer.split`: Sub-span tracking sentence-splitting efficiency.
- `nli_scoring`: Sub-span tracking cross-encoder inference runtime, chunk count, and batches.
