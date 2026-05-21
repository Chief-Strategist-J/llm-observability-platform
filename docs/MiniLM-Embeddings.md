# MiniLM Embeddings

For sampled, non-PII spans, the SDK asynchronously generates a **384-dimensional MiniLM-L6-v2 vector embedding** of the prompt text. This enables semantic similarity search, clustering, and prompt deduplication in your analytics databases.

---

## Async Generation Lifecycle

The embedding generation process runs entirely in the background, ensuring your application flow remains unblocked:

```
[Span Exits Context]
         │
         ▼
[Check Sampling/PII] ───(Failed)───► [Finalize & Report Span (No Embedding)]
         │
      (Passed)
         ▼
[Launch Asyncio Task] ─────────────► [Make HTTP POST to Embedding Worker]
         │                                      │
         │ (Application continues)              ├── (Success) ──► Attach 384 floats
         ▼                                      │
[Your Code Continues]                           └── (Timeout / Failure) ──► None
                                                        │
                                                        ▼
                                           [Report Enriched Payload]
```

---

## Automatic Embeddings (Inside Spans)

If the span passes the sampling gate and is free of PII, the SDK handles the task creation and network call automatically:

```python
from instrumentation_sdk import llm_span

async with llm_span(
    model="gpt-4o",
    provider="openai",
    prompt="Explain the attention mechanism in transformers."
) as span:
    response = await client.chat.completions.create(...)

# After the span exits:
# span._data["prompt_embedding"] contains a list of 384 floats (or None on failure/timeout)
```

---

## Direct Programmatic Usage

Generate embeddings on-demand outside of a span context using `get_embedding`:

```python
from instrumentation_sdk import get_embedding

async def main():
    vector = await get_embedding("What is the capital of France?")
    if vector:
        print(f"Vector Dimensions: {len(vector)}")  # Output: 384
        print(f"Slice: {vector[:5]}")
```

---

## Configuring the Embedding Worker URL

By default, the SDK points to `http://localhost:8000/embed`. You can customize this target via environment variables:

```bash
export EMBEDDING_WORKER_URL=http://my-embedding-service:8080
```

Or pass it into your Docker run command:
```bash
docker run -e EMBEDDING_WORKER_URL=http://embedding:8080 chiefj/instrumentation-sdk-api:latest
```

!!! note "Performance Defaults"
    - The connection has a hard **500 ms timeout** threshold.
    - If the worker fails or times out, the span is reported with `prompt_embedding: null` to avoid data loss.

---

## Vector Similarity Search Examples

Embeddings can be queried in downstream databases to discover similar prompt intents or group requests.

### PostgreSQL (using `pgvector`)

```sql
SELECT span_id, model, service_name,
       prompt_embedding <=> '[0.021, -0.103, 0.044, ...]'::vector AS cosine_distance
FROM llm_spans
WHERE is_sampled = true
  AND pii_detected = false
ORDER BY cosine_distance
LIMIT 5;
```

### ClickHouse

```sql
SELECT span_id, model, service_name,
       cosineDistance(prompt_embedding, [0.021, -0.103, 0.044, ...]) AS distance
FROM llm_spans
WHERE is_sampled = 1
  AND pii_detected = 0
ORDER BY distance ASC
LIMIT 5;
```

---

## Next Steps

- [Prometheus Metrics & Grafana](Prometheus-Metrics-and-Grafana.md) - Visualize span volume and costs.
- [REST Management API](REST-Management-API.md) - Embed and scan prompts using HTTP endpoints.
