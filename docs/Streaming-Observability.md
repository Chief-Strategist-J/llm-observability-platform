# Streaming Observability

Track streaming LLM responses with automatic **Time-to-First-Token (TTFT)** capture and completion token counting — without blocking your stream consumers.

---

## How It Works

The SDK wraps your generator/async-generator in a thin observable iterator that:
1. Records **TTFT** the moment the first chunk is yielded
2. Accumulates text chunks and counts completion tokens on the fly
3. Finalizes and reports the span when the stream ends, is closed early, or raises

Your consumer code doesn't change — just wrap the stream.

---

## Sync Streaming

```python
from instrumentation_sdk import llm_streaming_span, wrap_stream

def stream_response(prompt: str):
    with llm_streaming_span(
        model="gpt-4o",
        provider="openai",
        prompt=prompt
    ) as span_ctx:

        raw_stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        wrapped = wrap_stream(raw_stream, span_context=span_ctx, model="gpt-4o")

        for chunk in wrapped:
            text = chunk.choices[0].delta.content or ""
            print(text, end="", flush=True)

    # Span reported here: latency_ms_total, latency_ms_ttft, completion_tokens
```

---

## Async Streaming

```python
from instrumentation_sdk import llm_streaming_span, wrap_async_stream

async def stream_response(prompt: str):
    async with llm_streaming_span(
        model="gpt-4o",
        provider="openai",
        prompt=prompt
    ) as span_ctx:

        raw_stream = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        wrapped = wrap_async_stream(raw_stream, span_context=span_ctx, model="gpt-4o")

        async for chunk in wrapped:
            text = chunk.choices[0].delta.content or ""
            print(text, end="", flush=True)
```

---

## Custom Text Extractor

If your stream chunks aren't standard OpenAI objects, pass an extractor function:

```python
def my_extractor(chunk) -> str:
    return chunk.get("delta", {}).get("text", "")

wrapped = wrap_async_stream(
    raw_stream,
    span_context=span_ctx,
    model="gpt-4o",
    extract_text_fn=my_extractor
)
```

---

## Set Metadata Mid-Stream

You can call `set_metadata` while the stream is still running:

```python
async with llm_streaming_span(model="gpt-4o", provider="openai") as span_ctx:
    wrapped = wrap_async_stream(raw_stream, span_context=span_ctx, model="gpt-4o")
    async for chunk in wrapped:
        if chunk.model:
            span_ctx.set_metadata("actual_model", chunk.model)
        yield chunk.choices[0].delta.content or ""
```

---

## Early Close / Abort Resilience

If a consumer closes the stream before it's exhausted, the SDK still captures all tokens generated up to that point:

```python
wrapped = wrap_stream(raw_stream, span_context=span_ctx, model="gpt-4o")

for i, chunk in enumerate(wrapped):
    print(chunk)
    if i == 2:
        wrapped.close()   # span finalized here with partial token count
        break
```

Async version:
```bash
await wrapped.aclose()
```

---

## What Gets Captured

| Field | Description |
|---|---|
| `latency_ms_total` | Wall clock from span start to stream exhaustion |
| `latency_ms_ttft` | Time from span start to first chunk yielded |
| `completion_tokens` | Token count of accumulated text (tiktoken or estimated) |
| `token_count_method` | `tiktoken` or `estimated` |
| `status` | `success` or `error` |

---

## Try It via REST

Trigger a mock streaming call and see SSE events:

```bash
curl -X POST http://localhost:8002/v1/streaming/test-stream-call \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "chunks": ["Hello", " world", "!"]}'
```

Response (SSE):
```
data: Hello

data:  world

data: !
```

The SDK captures TTFT and token count for those chunks and reports the span.

---

## Notes

- `llm_streaming_span` returns an `LLMStreamingSpanContext` — a subclass of `LLMSpanContext`, so all `set_metadata` calls work the same way.
- Span finalization is idempotent — closing or exhausting the stream multiple times is safe.
- Token counting uses `tiktoken` when the model is recognized, falls back to character heuristics otherwise.

---

## Next: [PII & Injection Scanning](PII-and-Injection-Scanning)
