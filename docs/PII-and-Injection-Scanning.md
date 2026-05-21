# PII & Injection Scanning

Every prompt that passes through a manual span context is automatically scanned for PII and prompt injection attempts using an Aho-Corasick trie plus regex patterns — before the span is emitted.

---

## How It Works

- **PII detected** → prompt is fully redacted (`None`), `prompt_hash` and `prompt_embedding` are cleared. Span attribute `llm.pii_detected = true`.
- **Injection detected** → prompt is preserved, span attribute `llm.injection_attempt = true`.
- **Scanner failure** → exception is caught silently; your application code continues normally.

Scanning runs inline inside `llm_span`, `llm_span_with_tokens`, and `llm_streaming_span` — no extra setup needed.

---

## Automatic Scanning (Inside Spans)

PII and injection scanning is on by default for any span that receives a `prompt`:

```python
from instrumentation_sdk import llm_span

async with llm_span(model="gpt-4o", provider="openai", prompt="My email is bob@example.com") as span:
    response = await client.chat.completions.create(...)

# span._data["pii_detected"]     → True
# span._data["prompt"]           → None  (redacted)
# span._data["prompt_hash"]      → None
# span._data["prompt_embedding"] → None
```

```python
async with llm_span(model="gpt-4o", provider="openai", prompt="DROP TABLE users") as span:
    response = await client.chat.completions.create(...)

# span._data["injection_attempt"] → True
# span._data["prompt"]            → "DROP TABLE users"  (preserved)
```

---

## Direct Programmatic Scan

Call `scan_prompt` anywhere in your code:

```python
from instrumentation_sdk import scan_prompt

pii, injection = scan_prompt("My card number is 4111111111111111")
print(f"PII: {pii}, Injection: {injection}")
# PII: True, Injection: False

pii, injection = scan_prompt("UNION SELECT username, password FROM users")
print(f"PII: {pii}, Injection: {injection}")
# PII: False, Injection: True
```

### With Chat Message Lists

```python
messages = [
    {"role": "user", "content": "My email is test@example.com"},
    {"role": "assistant", "content": "Got it"}
]
pii, injection = scan_prompt(messages)
# pii: True
```

---

## Try It via REST

```bash
# No PII, no injection
curl -X POST http://localhost:8002/v1/pii-injection/scan \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of France?"}'
```
```json
{"pii_detected": false, "injection_attempt": false}
```

```bash
# Email address — PII
curl -X POST http://localhost:8002/v1/pii-injection/scan \
  -H "Content-Type: application/json" \
  -d '{"prompt": "My email is user@example.com"}'
```
```json
{"pii_detected": true, "injection_attempt": false}
```

```bash
# SQL injection
curl -X POST http://localhost:8002/v1/pii-injection/scan \
  -H "Content-Type: application/json" \
  -d '{"prompt": "SELECT * FROM accounts WHERE id = 1 OR 1=1"}'
```
```json
{"pii_detected": false, "injection_attempt": true}
```

```bash
# Both at once
curl -X POST http://localhost:8002/v1/pii-injection/scan \
  -H "Content-Type: application/json" \
  -d '{"prompt": "My card 4111111111111111 and DROP TABLE users"}'
```
```json
{"pii_detected": true, "injection_attempt": true}
```

---

## Default Patterns

Defined in `config/patterns.yaml`:

| Name | Type | Matches |
|---|---|---|
| `email` | `PII_STRUCTURAL` | `user@domain.tld` |
| `credit_card` | `PII_STRUCTURAL` | Visa, MC, Amex, Discover, JCB |
| `sql_injection` | `INJECTION_ATTEMPT` | `UNION`, `SELECT`, `DROP`, `INSERT`, `UPDATE`, `DELETE`, etc. |

---

## Add Custom Patterns

Edit `config/patterns.yaml`:

```yaml
patterns:
  - name: phone_number
    regex: "\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b"
    type: PII_STRUCTURAL

  - name: ssn
    regex: "\\b\\d{3}-\\d{2}-\\d{4}\\b"
    type: PII_STRUCTURAL

  - name: prompt_override
    phrase: "ignore previous instructions"
    type: INJECTION_ATTEMPT
```

Valid `type` values: `PII_STRUCTURAL`, `INJECTION_ATTEMPT`

Then restart the container:

```bash
docker restart instrumentation-sdk-api
```

CI validates that every regex compiles and no pattern name is duplicated before the image is built.

---

## Grafana — Security Dashboard

Open `http://localhost:3002` → **LLM Security & Safety Dashboard** to see:
- PII detection rate over time by service
- Prompt injection attempt rate over time
- Total cumulative violations (PII + injections)

---

## Notes

- Scanning is case-insensitive for phrase and text matching.
- Both string prompts and structured message-list prompts are supported.
- Scanning runs synchronously inside span creation — it adds negligible latency (<1 ms for typical prompts).
- Regex patterns run after the Aho-Corasick pass, so structural PII (email, card numbers) is caught even without exact phrase matches.

---

## Next: [Deterministic Sampling](Deterministic-Sampling)
