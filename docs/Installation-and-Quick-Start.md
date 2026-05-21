# Installation & Quick Start

Get your first span captured in under 5 minutes.

---

## Install

```bash
pip install instrumentation-sdk
```

---

## Option A — Auto-Instrumentation (Zero Code Changes)

Drop this at the top of your app. Every OpenAI / Anthropic / LiteLLM / LangChain call is tracked automatically.

```python
from instrumentation_sdk import init_auto_instrumentation

init_auto_instrumentation()  # call once, at startup

# From here, all LLM calls are tracked — no other changes needed
import openai
client = openai.AsyncOpenAI()
response = await client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## Option B — Manual Span (Decorator)

```python
from instrumentation_sdk import llm_observe

@llm_observe(service="my-app", endpoint="chat")
async def ask_llm(prompt: str):
    # your existing LLM code here
    return response
```

---

## Option C — Manual Span (Context Manager)

```python
from instrumentation_sdk import llm_span

async with llm_span(model="gpt-4o", provider="openai") as span:
    response = await client.chat.completions.create(...)
    span.set_metadata("prompt_tokens", response.usage.prompt_tokens)
```

---

## Verify It's Working

### 1. Start the all-in-one observability stack

```bash
llm-observe start
```

This launches:
- **API** → `http://localhost:8002`
- **Grafana** → `http://localhost:3002`

### 2. Trigger a test span via curl

```bash
curl -X POST http://localhost:8002/v1/instrumentation/test-call \
  -H "Content-Type: application/json" \
  -d '{"method": "httpx", "provider": "openai"}'
```

Expected response:
```json
{"success": true, "message": "Test call triggered via httpx for openai"}
```

### 3. Check Grafana

Open `http://localhost:3002` → **LLM Observability** folder → pick any dashboard.  
Spans appear within 5–10 seconds.

---

## Supported LLM Providers (Auto-Instrumentation)

| Provider | Client | What's patched |
|---|---|---|
| OpenAI | `openai.AsyncOpenAI` / `openai.OpenAI` | `chat.completions.create` |
| Anthropic | `anthropic.AsyncAnthropic` / `anthropic.Anthropic` | `messages.create` |
| LiteLLM | `litellm` module | `acompletion` / `completion` |
| LangChain | Any `BaseChatModel` subclass | `ainvoke` / `invoke` |
| Generic HTTP | `httpx`, `requests` | Any call matching known LLM URLs |

---

## Next Steps

- [Auto-Instrumentation](Auto-Instrumentation) — detailed provider config
- [Manual Spans — Context Manager](Manual-Spans-Context-Manager) — set metadata mid-call
- [Docker & CLI Deployment](Docker-and-CLI-Deployment) — production deployment
