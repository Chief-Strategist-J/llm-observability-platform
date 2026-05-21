# Manual Spans — Decorator

Use `@llm_observe` to track any function with a single line. Works with sync and async functions.

---

## Basic Usage

```python
from instrumentation_sdk import llm_observe

@llm_observe(service="payment-bot", endpoint="summarize")
def summarize(text: str) -> str:
    # your LLM call here
    return result
```

```python
# Async version — identical decorator, just add async
@llm_observe(service="search-agent", endpoint="answer")
async def answer(question: str) -> str:
    response = await client.chat.completions.create(...)
    return response.choices[0].message.content
```

**What's captured automatically:**
- `span_id` (UUID)
- `service_name` from `service=`
- `endpoint` from `endpoint=`
- `latency_ms_total`
- `status` — `"success"` or `"error"`
- `timestamp_utc`
- `is_sampled` (deterministic, SHA-256 gate)

---

## Class Methods

Works on instance methods without any changes:

```python
class LLMService:
    @llm_observe(service="chat-api", endpoint="respond")
    async def respond(self, user_id: str, prompt: str) -> str:
        return await self._call_llm(prompt)
```

---

## Error Tracking

If the decorated function raises, the span is still emitted with `status="error"`:

```python
@llm_observe(service="agent", endpoint="plan")
async def plan(goal: str):
    raise ValueError("LLM quota exceeded")  # span emitted, status=error
```

---

## Nested Spans

Each decorated call gets its own unique `span_id`:

```python
@llm_observe(service="pipeline", endpoint="outer")
async def outer():
    result = await inner()   # inner gets its own span
    return result

@llm_observe(service="pipeline", endpoint="inner")
async def inner():
    return await client.chat.completions.create(...)
```

Two spans are reported — `outer` and `inner` — each with independent latency.

---

## Concurrent Calls

Fully safe for concurrent execution — spans are isolated per call:

```python
import asyncio

@llm_observe(service="batch", endpoint="classify")
async def classify(text: str):
    return await client.chat.completions.create(model="gpt-4o", messages=[...])

# All 10 calls get independent spans
results = await asyncio.gather(*[classify(t) for t in texts])
```

---

## When to Use the Decorator vs Context Manager

| Use `@llm_observe` when… | Use `llm_span` when… |
|---|---|
| You want minimal code change | You need to set metadata after the LLM responds (e.g. actual model used, token counts) |
| Function boundary = span boundary | You need mid-call updates |
| Simple success/error tracking is enough | You need streaming support |

---

## Verify via REST

Trigger a test span without writing code:

```bash
curl -X POST http://localhost:8002/v1/instrumentation/test-call \
  -H "Content-Type: application/json" \
  -d '{"method": "httpx", "provider": "openai"}'
```

Check sampling status for a span ID:

```bash
curl -X POST http://localhost:8002/v1/sampling/should-sample \
  -H "Content-Type: application/json" \
  -d '{"span_id": "your-span-id-here"}'
```

Response:
```json
{"is_sampled": false}
```

---

## Next: [Manual Spans — Context Manager](Manual-Spans-Context-Manager)
