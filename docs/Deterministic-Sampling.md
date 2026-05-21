# Deterministic Sampling

The SDK uses a deterministic SHA-256 gate to decide which spans qualify for downstream vector embedding generation and prompt hashing. This minimizes CPU and memory consumption while ensuring statistical representation.

---

## Sampling Gate Logic

```
          Span ID (UUID / String / Bytes)
                        │
                        ▼
                  [SHA-256 Hash]
                        │
                        ▼
               [Convert to Integer]
                        │
                        ▼
                  [Modulo 100] ───► Result (0 - 99)
                        │
                        ▼
                   ( == 0 ? )
             ┌──────────┴──────────┐
             ▼                     ▼
          ( Yes )                ( No )
             │                     │
             ▼                     ▼
       is_sampled=True       is_sampled=False
       [Full Metrics,        [Full Metrics,
        Embeddings,           No Embeddings,
        Prompt Hashes]        No Prompt Hashes]
```

- Roughly **1% of spans** are sampled.
- The outcome is **deterministic** — the same `span_id` will always yield the identical sampling state.
- Unsampled spans are still reported to the dashboards; they simply skip vector/hash compute cycles.

---

## Feature Matrix by Sampling State

| Operation / Field Captured | Sampled (`True`) | Unsampled (`False`) |
|---|:---:|:---:|
| **Latency Tracking (`latency_ms_total`)** | ✅ Captured | ✅ Captured |
| **Token Tracking (`prompt_tokens`, etc.)** | ✅ Captured | ✅ Captured |
| **USD Cost Calculation** | ✅ Calculated | ✅ Calculated |
| **PII & Injection Scan** | ✅ Scanned | ✅ Scanned |
| **Prompt SHA-256 Hash (`prompt_hash`)** | ✅ Computed | ❌ `None` |
| **384-dim Embeddings (`prompt_embedding`)** | ✅ Generated | ❌ Skipped |

---

## Programmatic Usage

Check if a given ID would pass the sampling gate:

```python
from instrumentation_sdk import should_sample
import uuid

# Check a newly generated UUID
span_id = uuid.uuid4()
sampled = should_sample(span_id)
print(f"Span {span_id} -> sampled: {sampled}")
```

`should_sample` accepts various formats:

| Format | Example |
|---|---|
| `uuid.UUID` | `uuid.uuid4()` |
| `str` (UUID format) | `"550e8400-e29b-41d4-a716-446655440000"` |
| `str` (generic) | `"user-session-1234"` |
| `bytes` | `b"\x12\x34..."` |

---

## Behavior Inside Spans

Sampling is run automatically when initializing a span. You can read the state directly from the span properties:

```python
async with llm_span(model="gpt-4o", provider="openai") as span:
    print(span._data["is_sampled"])  # True or False
```

!!! note "PII Scan Precedence"
    If PII is detected, the SDK immediately redacts the prompt text and clears the hashes/embeddings, **even if the span was selected by the sampling gate**.

---

## Verification via REST API

Check the gate status for any ID using curl:

```bash
curl -X POST http://localhost:8002/v1/sampling/should-sample \
  -H "Content-Type: application/json" \
  -d '{"span_id": "00000000-0000-0000-0000-000000000000"}'
```

Response:
```json
{"is_sampled": false}
```

---

## Next Steps

- [MiniLM Embeddings](MiniLM-Embeddings.md) - Learn how sampled prompts are vector-mapped.
- [Prometheus Metrics & Grafana](Prometheus-Metrics-and-Grafana.md) - Visualizing sampled metric rates.
