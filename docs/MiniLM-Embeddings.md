# MiniLM Embeddings

For sampled, non-PII spans, the SDK asynchronously generates a **384-dimensional MiniLM-L6-v2 vector embedding** of the prompt text. This enables semantic similarity search, clustering, and prompt deduplication in your analytics layer.

---

## How It Works

1. Span finalization checks: `is_sampled == True` AND `pii_detected == False` AND `prompt` is not empty.
2. If all three pass, `get_embedding(prompt)` is fired as a **non-blocking background task** using `asyncio.create_task()`.
3. The embedding HTTP call has a **500 ms timeout**. If it times out or fails, `prompt_embedding` is set to `None` and the rest of the span is emitted normally.
4. The embedding is stored in `span_data["prompt_embedding"]` — a list of 384 floats.

---

## Automatic Embedding (Inside Spans)

No setup needed. If the span is sampled and has no PII, the embedding is generated automatically:

```python
from instrumentation_sdk import llm_span

async with llm_span(
    model="gpt-4o",
    provider="openai",
    prompt="Explain the transformer architecture."
) as span:
    response = await client.chat.completions.create(...)

# After span exit:
# span._data["prompt_embedding"] → [0.021, -0.103, 0.044, ...]  (384 floats)
# or None if unsampled / PII detected / timeout
```

---

## Direct Programmatic Usage

Call `get_embedding` directly when you need the vector outside of a span:

```python
from instrumentation_sdk import get_embedding

embedding = await get_embedding("What is the capital of France?")

if embedding:
    print(f"Dimensions: {len(embedding)}")   # 384
    print(f"First 5 values: {embedding[:5]}")
else:
    print("Embedding unavailable (timeout or worker down)")
```

---

## Try It via REST

```bash
curl -X POST http://localhost:8002/v1/embeddings/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "What is the capital of France?"}'
```

Response:
```json
{
  "embedding": [0.021, -0.103, 0.044, 0.189, -0.012, "...383 more values..."]
}
```

If the embedding worker is unreachable:
```json
{"detail": "Failed to generate embedding"}
```

---

## Concurrency Model

The embedding call is non-blocking — your application doesn't wait for it:

```python
# Timeline:
# t=0ms  → span exits, span data written, metrics recorded
# t=0ms  → asyncio.create_task(get_embedding(prompt))  ← fires in background
# t=0ms  → your code continues immediately
# t=~80ms → embedding arrives, reporter.report_async(span_data) called
```

In a synchronous context (e.g. sync `llm_span`), a background thread is used instead of a task.

---

## Conditions That Skip Embedding

| Condition | Embedding generated? |
|---|---|
| `is_sampled == False` | ❌ No |
| `pii_detected == True` | ❌ No |
| `prompt` is `None` or empty | ❌ No |
| Embedding worker unreachable | ❌ No (falls back to `None`) |
| Embedding worker times out (>500 ms) | ❌ No (falls back to `None`) |
| All conditions pass | ✅ Yes |

---

## Configure the Embedding Worker URL

By default the SDK calls `http://localhost:8000/embed`. Override with an environment variable:

```bash
export EMBEDDING_WORKER_URL=http://my-embedding-service:8080
```

Or in Docker:
```bash
docker run -e EMBEDDING_WORKER_URL=http://embedding:8080 chiefj/instrumentation-sdk-api:latest
```

---

## Using Embeddings for Similarity Search

Once stored in ClickHouse or PostgreSQL (via the `prompt_embedding vector(384)` column), you can find semantically similar prompts:

```sql
-- PostgreSQL with pgvector
SELECT span_id, model, service_name,
       prompt_embedding <=> '[0.021, -0.103, ...]'::vector AS distance
FROM llm_spans
WHERE is_sampled = true
  AND pii_detected = false
ORDER BY distance
LIMIT 10;
```

---

## Notes

- The embedding model is **MiniLM-L6-v2** via Cloudflare Workers AI — 384 dimensions, fast inference.
- Embeddings are only stored for the **1% sampled** spans that also have no PII. This keeps storage costs manageable at high throughput.
- The `response_embedding` field follows the same pattern but requires you to set it manually via `span.set_metadata("response_embedding", vector)` after receiving the LLM response.

---

## Next: [Prometheus Metrics & Grafana](Prometheus-Metrics-and-Grafana)
