# Manual Spans — Context Manager

Use `llm_span` when you need to set metadata **after** the LLM responds — e.g. actual model used, token counts from the response, or custom fields. Use `llm_span_with_tokens` to also get automatic pre-call token counting.

---

## `llm_span` — Basic

```python
from instrumentation_sdk import llm_span

async def handle_request(user_id: str, prompt: str):
    async with llm_span(model="gpt-4o", provider="openai", user_id=user_id) as span:

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )

        # Set metadata from the actual response
        span.set_metadata("prompt_tokens", response.usage.prompt_tokens)
        span.set_metadata("completion_tokens", response.usage.completion_tokens)
        span.set_metadata("actual_model", response.model)

    # Span is reported here automatically (even on exception)
    return response.choices[0].message.content
```

**`set_metadata` works for any key.** Common ones:

| Key | Type | Notes |
|---|---|---|
| `prompt_tokens` | `int` | Exact count from response |
| `completion_tokens` | `int` | Exact count from response |
| `actual_model` | `str` | Model the provider actually used |
| `session_id` | `str` | Conversation thread ID |
| `finish_reason` | `str` | `stop`, `length`, `content_filter` |
| `retry_count` | `int` | Number of retries before success |

---

## `llm_span` — Sync

Works identically without `async`:

```python
with llm_span(model="gpt-4o", provider="openai") as span:
    response = client.chat.completions.create(...)
    span.set_metadata("prompt_tokens", response.usage.prompt_tokens)
```

---

## `llm_span_with_tokens` — Automatic Token Pre-Counting

Counts prompt tokens **before** the LLM call and records `prompt_tokens` and `token_count_method` automatically.

```python
from instrumentation_sdk import llm_span_with_tokens

async def handle(prompt: str):
    async with llm_span_with_tokens(
        model="gpt-4o",
        provider="openai",
        prompt=prompt          # tokens are counted here, before the call
    ) as span:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        # prompt_tokens already set — just add completion side
        span.set_metadata("completion_tokens", response.usage.completion_tokens)
```

Token counting falls back to character-based heuristics if `tiktoken` doesn't recognise the model.

---

## With Chat Message Lists

Both `llm_span_with_tokens` and the REST endpoint handle structured message arrays:

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain transformers in one paragraph."}
]

async with llm_span_with_tokens(
    model="gpt-4o",
    provider="openai",
    prompt=messages          # list format accepted
) as span:
    response = await client.chat.completions.create(model="gpt-4o", messages=messages)
```

---

## Error Handling

The span is always reported, even when the block raises:

```python
async with llm_span(model="gpt-4o", provider="openai") as span:
    raise TimeoutError("Provider timeout")
# span emitted with status="error"
```

---

## Nested Spans

```python
async with llm_span(model="router", service_name="orchestrator") as parent:
    async with llm_span(model="gpt-4o", service_name="worker") as child:
        response = await client.chat.completions.create(...)
        child.set_metadata("completion_tokens", response.usage.completion_tokens)
    parent.set_metadata("child_model", "gpt-4o")
# child span emitted first, parent span emitted second
```

---

## Manual Reporter (Advanced)

If you need direct control over the span payload:

```python
from instrumentation_sdk import get_reporter

reporter = get_reporter()
await reporter.report_async({
    "span_id": "550e8400-e29b-41d4-a716-446655440000",
    "service_name": "my-service",
    "model": "gpt-4o",
    "provider": "openai",
    "status": "success",
    "latency_ms_total": 312,
    "prompt_tokens": 45,
    "completion_tokens": 120,
})
```

---

## Try It via REST

Count tokens without writing code:

```bash
# Plain string
curl -X POST http://localhost:8002/v1/token-counting/count \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain transformers in one paragraph.", "model": "gpt-4o"}'
```

Response:
```json
{"tokens": 9, "method": "tiktoken"}
```

```bash
# Chat message list
curl -X POST http://localhost:8002/v1/token-counting/count \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain transformers."}
    ],
    "model": "gpt-4o"
  }'
```

Response:
```json
{"tokens": 22, "method": "tiktoken"}
```

---

## Next: [Streaming Observability](Streaming-Observability)
