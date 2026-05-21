# Streaming Observability

Track streaming LLM responses with automatic **Time-to-First-Token (TTFT)** capture and completion token counting — without blocking your stream consumers.

---

## Streaming Lifecycle & Timeline

The SDK wraps your stream generator/async-generator in a thin wrapper that captures metrics at key points in the stream's lifecycle:

```
[Start context: llm_streaming_span()]
           │
           ▼
[Launch API Request]
           │
           ▼
[Yield First Chunk]  ────────► Record TTFT (Time-to-First-Token)
           │
           ▼
[Yield Next Chunks]  ────────► Accumulate content string in background
           │
           ▼
[Stream Ends / Aborts] ──────► Count total completion tokens (tiktoken/est)
           │                   Compute total request latency
           ▼
 [Span Emitted to API]
```

---

## Sync Streaming

Use `llm_streaming_span` along with `wrap_stream` to wrap a synchronous generator:

```python
from instrumentation_sdk import llm_streaming_span, wrap_stream

def stream_response(prompt: str):
    with llm_streaming_span(model="gpt-4o", provider="openai", prompt=prompt) as span_ctx:
        # Outbound call with stream=True
        raw_stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        # Wrap the stream to intercept yields
        wrapped = wrap_stream(raw_stream, span_context=span_ctx, model="gpt-4o")

        for chunk in wrapped:
            text = chunk.choices[0].delta.content or ""
            print(text, end="", flush=True)

    # Span is reported at this point (including TTFT and completion tokens)
```

---

## Async Streaming

Wrap async generators using `wrap_async_stream`:

```python
from instrumentation_sdk import llm_streaming_span, wrap_async_stream

async def stream_response(prompt: str):
    async with llm_streaming_span(model="gpt-4o", provider="openai", prompt=prompt) as span_ctx:
        # Outbound async call
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

## Custom Text Extractors

If you are using a provider whose stream chunks don't match standard OpenAI structures, pass a custom `extract_text_fn` handler:

```python
# Custom extractor mapping chunk dictionary keys
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

## Early Aborts & Cleanups

If a user or application closes the stream before it finishes, the SDK captures the partial output and emits the span immediately with the accrued token counts:

```python
wrapped = wrap_stream(raw_stream, span_context=span_ctx, model="gpt-4o")

for i, chunk in enumerate(wrapped):
    print(chunk)
    if i == 5:
        wrapped.close()  # Finalizes the span and uploads collected telemetry
        break
```

!!! note "Async Early Close"
    For async generators, call `await wrapped.aclose()` to trigger the same finalization behavior.

---

## Telemetry Attributes

Streaming spans capture the following core metrics:

| Attribute | Type | Description |
|---|---|---|
| `latency_ms_total` | `int` | Duration from span start to stream exhaustion/closure |
| `latency_ms_ttft` | `int` | Duration from span start to first yielded chunk |
| `completion_tokens` | `int` | Computed from accumulated stream content |
| `token_count_method` | `str` | `"tiktoken"` or `"estimated"` |

---

## Next Steps

- [PII & Injection Scanning](../features/PII-and-Injection-Scanning.md) — Prevent data leaks and input injections.
- [Deterministic Sampling](../features/Deterministic-Sampling.md) — Optimize resource usage with the 1% gate.
