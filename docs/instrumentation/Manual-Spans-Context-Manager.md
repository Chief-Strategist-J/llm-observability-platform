# Manual Spans — Context Manager

Use context managers when you need dynamic span properties or need to set metadata **after** the LLM responds (such as actual tokens consumed, custom session IDs, or embedding vectors).

---

## Token Pre-Counting & Logging Pipeline

When using `llm_span_with_tokens`, the SDK performs token counting before making the outbound LLM call:

```
[Prompt Passed to Context Manager]
                │
                ▼
      [Tiktoken Matcher] ──(Fails/Unknown Model)──► [Estimate (Char Heuristic)]
                │                                             │
                ├──(Success)                                  │
                ▼                                             ▼
       [Exact Token Count]                           [Heuristic Token Count]
                │                                             │
                └───────────────┬─────────────────────────────┘
                                │
                                ▼
                   [Span Metadata Recorded]
                    - prompt_tokens
                    - token_count_method
                                │
                                ▼
                      [Outbound LLM Call]
```

---

## `llm_span` — Basic Usage

The standard context manager lets you set metadata dynamically using `span.set_metadata(key, value)`.

```python
from instrumentation_sdk import llm_span

async def handle_request(user_id: str, prompt: str):
    async with llm_span(model="gpt-4o", provider="openai", user_id=user_id) as span:
        # Outbound call to LLM
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )

        # Log details retrieved from the response object
        span.set_metadata("prompt_tokens", response.usage.prompt_tokens)
        span.set_metadata("completion_tokens", response.usage.completion_tokens)
        span.set_metadata("actual_model", response.model)

    return response.choices[0].message.content
```

!!! note "Metadata Keys"
    `set_metadata` accepts any string key. Standard dashboard keys are:
    
    | Key | Type | Description |
    |---|---|---|
    | `prompt_tokens` | `int` | Input token count |
    | `completion_tokens` | `int` | Output token count |
    | `actual_model` | `str` | Exact model name returned by the provider |
    | `session_id` | `str` | Logical conversation/thread grouping |
    | `finish_reason` | `str` | e.g. `stop`, `length`, `content_filter` |
    | `retry_count` | `int` | Number of attempts made |

---

## `llm_span_with_tokens` — Automatic Token Pre-Counting

Use `llm_span_with_tokens` to count prompt tokens locally **before** the LLM call is executed. This records `prompt_tokens` and `token_count_method` automatically.

```python
from instrumentation_sdk import llm_span_with_tokens

async def handle(prompt: str):
    async with llm_span_with_tokens(
        model="gpt-4o",
        provider="openai",
        prompt=prompt  # String prompt passed directly
    ) as span:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        # prompt_tokens is already computed — just log completion tokens
        span.set_metadata("completion_tokens", response.usage.completion_tokens)
```

!!! tip "Chat Message Support"
    `llm_span_with_tokens` handles both plain strings and structured message lists:
    
    ```python
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain transformers in a sentence."}
    ]
    
    async with llm_span_with_tokens(
        model="gpt-4o",
        provider="openai",
        prompt=messages  # Supported automatically
    ) as span:
        ...
    ```

---

## Synchronous Context Manager

If you are not using `asyncio`, both context managers can be used in synchronous blocks without the `async` prefix:

```python
from instrumentation_sdk import llm_span

with llm_span(model="gpt-4o", provider="openai") as span:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    span.set_metadata("prompt_tokens", response.usage.prompt_tokens)
```

---

## Error Handling

If an exception occurs within the context block, the span is automatically finalized, marked with `status="error"`, and reported before the exception bubbles up:

```python
async with llm_span(model="gpt-4o", provider="openai") as span:
    # This will trigger an error span to be emitted
    raise TimeoutError("Provider failed to respond")
```

---

## Nested Context Managers

Context managers can be nested to capture hierarchical multi-agent or router-worker topologies:

```python
async with llm_span(model="router-v2", service_name="agent-router") as parent:
    # Router logic
    async with llm_span(model="gpt-4o", service_name="writer-agent") as child:
        # Worker logic
        response = await client.chat.completions.create(...)
        child.set_metadata("completion_tokens", response.usage.completion_tokens)
```

---

## Token Counting Endpoint

You can query the SDK's token counting engine directly via REST:

```bash
curl -X POST http://localhost:8002/v1/token-counting/count \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world!", "model": "gpt-4o"}'
```

Response:
```json
{"tokens": 3, "method": "tiktoken"}
```

---

## Next Steps

- [Streaming Observability](Streaming-Observability.md) — Tracking generators, async iterators, and TTFT.
- [PII & Injection Scanning](../features/PII-and-Injection-Scanning.md) — Masking sensitive data and preventing prompt exploits.
