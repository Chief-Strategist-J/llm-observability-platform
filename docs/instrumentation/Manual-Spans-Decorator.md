# Manual Spans — Decorator

Use the `@llm_observe` decorator to instrument any function with a single line of code. It automatically tracks execution time, inputs/outputs, and success or error states for both sync and async functions.

---

## Execution Flow

When a decorated function is called, the SDK wraps it in an execution handler that monitors its lifecycle:

```
[Function Called]
       │
       ▼
[Decorator @llm_observe] ────► Evaluates Sampling Gate (SHA-256 modulus)
       │                                     │
       │ (Runs Function)                     ▼
       ▼                               is_sampled?
[Execute Inner Function]               ┌─────┴─────┐
       │                               ▼           ▼
       ├──► Returns Success ──► status="success"   Yes          No
       │                               ▼           ▼
       └──► Raises Error    ──► status="error"     Generate     Skip
                                       │         Embeddings
                                       ▼           │
                              [Report Span to API]◄┘
```

---

## Basic Usage

### Synchronous Function

```python
from instrumentation_sdk import llm_observe

@llm_observe(service="payment-bot", endpoint="summarize")
def summarize(text: str) -> str:
    # Your LLM call or business logic here
    return "Summary of the text..."
```

### Asynchronous Function

```python
from instrumentation_sdk import llm_observe

@llm_observe(service="search-agent", endpoint="answer")
async def answer(question: str) -> str:
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content
```

!!! info "Captured Automatically"
    - **Span ID & Trace ID**: Unique UUIDs correlating the execution context.
    - **Service Name & Endpoint**: Configured in decorator arguments.
    - **Latency**: Total wall-clock time in milliseconds (`latency_ms_total`).
    - **Status**: `"success"` or `"error"`.
    - **Sampling Gate State**: `is_sampled` (1% deterministic sampling).

---

## Class Methods

The decorator works seamlessly on instance and class methods without disrupting `self` or `cls` arguments:

```python
class LLMService:
    def __init__(self, client):
        self.client = client

    @llm_observe(service="chat-api", endpoint="respond")
    async def respond(self, user_id: str, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
```

---

## Error and Exception Tracking

If the decorated function raises an exception, the span is still captured, labeled with `status="error"`, and reported before the exception is propagated:

```python
@llm_observe(service="agent", endpoint="plan")
async def plan(goal: str):
    # Span is captured and marked as status="error"
    raise ValueError("LLM quota exceeded")
```

---

## Nested Spans

When decorated functions call other decorated functions, the SDK automatically manages the parent-child relationships using tracing context:

```python
@llm_observe(service="pipeline", endpoint="outer")
async def outer_pipeline(prompt: str):
    # Both outer and inner functions emit separate spans
    result = await inner_processing(prompt)
    return result

@llm_observe(service="pipeline", endpoint="inner")
async def inner_processing(text: str):
    return await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": text}]
    )
```

---

## Concurrent Execution

The decorator is safe to use in highly concurrent async environments. Spans are isolated using task-local storage to prevent cross-contamination:

```python
import asyncio

@llm_observe(service="batch", endpoint="classify")
async def classify(text: str):
    return await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": text}]
    )

async def main():
    texts = ["Text A", "Text B", "Text C"]
    # All 3 calls get independent, isolated spans
    results = await asyncio.gather(*[classify(t) for t in texts])
```

---

## Decorator vs. Context Manager

| Feature | `@llm_observe` Decorator | `llm_span` Context Manager |
|---|---|---|
| **Code Footprint** | Minimal (single decorator line) | Wraps specific code block |
| **Span Scope** | Entire function boundary | Inside block boundary |
| **Response Logging** | Automatic success/error status | Manual metadata logging (`span.set_metadata`) |
| **Streaming Support** | ❌ Not recommended | ✅ Supported (`llm_streaming_span`) |
| **Dynamic Inputs** | ❌ Hardcoded decorator params | ✅ Dynamic params based on runtime state |

---

## Verification via REST

You can check the sampling status of any span ID using the management API:

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

## Next Steps

- [Manual Spans — Context Manager](Manual-Spans-Context-Manager.md) — Dynamic attributes and manual token counting.
- [Streaming Observability](Streaming-Observability.md) — Time-to-First-Token and streaming yield wrapping.
