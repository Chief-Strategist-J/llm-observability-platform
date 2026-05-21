# Deterministic Sampling

The SDK uses a deterministic SHA-256 gate to decide whether a span is "sampled" — meaning it qualifies for expensive downstream operations like prompt hashing and MiniLM embedding generation.

---

## How It Works

```
is_sampled = SHA256(span_id_bytes) % 100 == 0
```

- Roughly **1% of spans** are sampled.
- The result is **deterministic** — the same `span_id` always produces the same outcome.
- Unsampled spans are still fully reported; they just skip `prompt_hash` and `prompt_embedding` generation.

---

## What Changes Based on `is_sampled`

| Operation | Sampled (`True`) | Unsampled (`False`) |
|---|---|---|
| Span reported | ✅ Always | ✅ Always |
| `latency_ms_total`, tokens, cost | ✅ Always | ✅ Always |
| `prompt_hash` (SHA-256 of prompt) | ✅ Computed | ❌ `None` |
| `prompt_embedding` (384-dim MiniLM) | ✅ Generated | ❌ Skipped |
| `response_embedding` | ✅ Generated | ❌ Skipped |

This keeps the 99% unsampled path cheap while the 1% sampled path gets full semantic enrichment.

---

## Programmatic Usage

```python
from instrumentation_sdk import should_sample
import uuid

span_id = uuid.uuid4()
sampled = should_sample(span_id)
print(f"Span {span_id} → sampled: {sampled}")
```

`should_sample` accepts:

| Input type | Example |
|---|---|
| `uuid.UUID` | `uuid.uuid4()` |
| `str` (UUID format) | `"550e8400-e29b-41d4-a716-446655440000"` |
| `str` (arbitrary) | `"my-custom-span-id"` |
| `bytes` | `uuid.uuid4().bytes` |

All forms produce the same result for the same underlying value.

---

## Sampling is Automatic Inside Spans

You don't need to call `should_sample` manually — every `llm_span`, `llm_span_with_tokens`, `llm_streaming_span`, and `@llm_observe` call runs the gate automatically:

```python
async with llm_span(model="gpt-4o", provider="openai", prompt="Hello") as span:
    print(span._data["is_sampled"])   # True or False
    # If False: prompt_hash and prompt_embedding are already None
```

Calling `set_metadata("prompt_hash", ...)` on an unsampled span is silently ignored:

```python
async with llm_span(...) as span:
    if not span._data["is_sampled"]:
        span.set_metadata("prompt_hash", "abc...")  # no-op — dropped
```

---

## PII Overrides Sampling

Even if a span is sampled, PII detection overrides it — embeddings and hashes are always cleared when PII is found:

```python
async with llm_span(model="gpt-4o", prompt="email: bob@example.com") as span:
    pass
# span._data["is_sampled"]       → could be True
# span._data["pii_detected"]     → True
# span._data["prompt_hash"]      → None  (PII wins)
# span._data["prompt_embedding"] → None  (PII wins)
```

---

## Try It via REST

Check whether a specific span ID would be sampled:

```bash
curl -X POST http://localhost:8002/v1/sampling/should-sample \
  -H "Content-Type: application/json" \
  -d '{"span_id": "test-span-id"}'
```
```json
{"is_sampled": false}
```

```bash
# Try a UUID that is known to be sampled (hash % 100 == 0)
curl -X POST http://localhost:8002/v1/sampling/should-sample \
  -H "Content-Type: application/json" \
  -d '{"span_id": "00000000-0000-0000-0000-000000000000"}'
```

Finding a sampled ID quickly — run this in Python:
```python
import uuid
from instrumentation_sdk import should_sample

for _ in range(200):
    sid = uuid.uuid4()
    if should_sample(sid):
        print(sid)   # copy this into your curl
        break
```

---

## Distribution Check

Roughly 1 in 100 spans are sampled. You can verify the rate:

```python
import uuid
from instrumentation_sdk import should_sample

sampled = sum(1 for _ in range(10_000) if should_sample(uuid.uuid4()))
print(f"Sampled: {sampled}/10000 = {sampled/100:.1f}%")
# Sampled: ~100/10000 = ~1.0%
```

---

## Notes

- The gate is evaluated once at span creation time and stored in `span._data["is_sampled"]`.
- Changing a span's `is_sampled` value mid-span via `set_metadata` has no effect — the gate result is final.
- The 1% rate is fixed by the `% 100 == 0` condition. To change the rate, modify `sha256_sampling_adapter.py` and update the modulus.

---

## Next: [MiniLM Embeddings](MiniLM-Embeddings)
