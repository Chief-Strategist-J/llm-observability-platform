# PII & Injection Scanning

Protect user privacy and secure your models. Prompts passing through manual span contexts are scanned for PII (Personally Identifiable Information) and injection attempts using a combined Aho-Corasick prefix trie and regular expressions.

---

## Scanning Execution Flow

Scanning is executed synchronously before the span is finalized and emitted to the collection backend:

```
                  [Input Prompt / Messages]
                             │
                             ▼
                 [Aho-Corasick Phrase Match]
                             │
                             ▼
                    [Regex Pattern Match]
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
      [PII Detected?]               [Injection Detected?]
      ┌─────┴─────┐                     ┌─────┴─────┐
      ▼           ▼                     ▼           ▼
   ( Yes )      ( No )               ( Yes )      ( No )
      │           │                     │           │
      ▼           ▼                     ▼           ▼
Redact Prompt  No Change             Set Flag    No Flag
Clear Embeds                      injection_attempt
& Hashes                              = True
```

---

## Automatic Scanning (Inside Spans)

Any prompt passed to a context manager is scanned automatically:

```python
from instrumentation_sdk import llm_span

async with llm_span(model="gpt-4o", provider="openai", prompt="My email is alice@example.com") as span:
    response = await client.chat.completions.create(...)

# Attributes evaluated automatically:
# span._data["pii_detected"]     → True
# span._data["prompt"]           → None  (fully redacted)
# span._data["prompt_hash"]      → None  (cleared to prevent leaks)
# span._data["prompt_embedding"] → None
```

```python
async with llm_span(model="gpt-4o", provider="openai", prompt="DROP TABLE users;") as span:
    response = await client.chat.completions.create(...)

# Attributes evaluated automatically:
# span._data["injection_attempt"] → True
# span._data["prompt"]            → "DROP TABLE users;"  (preserved for analysis)
```

---

## Programmatic Verification

You can scan strings or structured chat history directly in your code using `scan_prompt`:

```python
from instrumentation_sdk import scan_prompt

# Scan a simple string prompt
pii_found, injection_found = scan_prompt("Contact me at test@example.com")
print(f"PII: {pii_found}, Injection: {injection_found}")
# Output: PII: True, Injection: False

# Scan structured chat messages
messages = [
    {"role": "user", "content": "SELECT * FROM secrets;"},
    {"role": "assistant", "content": "Access denied."}
]
pii_found, injection_found = scan_prompt(messages)
print(f"PII: {pii_found}, Injection: {injection_found}")
# Output: PII: False, Injection: True
```

---

## Default Patterns

The default pattern list is defined in `config/patterns.yaml`:

| Pattern Name | Type | Matching Strategy | Examples |
|---|---|---|---|
| `email` | `PII_STRUCTURAL` | Regex | `user@domain.tld`, `test.sub@host.co` |
| `credit_card` | `PII_STRUCTURAL` | Regex | Visa, Mastercard, AMEX, Discover |
| `sql_injection` | `INJECTION_ATTEMPT` | Regex | `UNION SELECT`, `DROP TABLE`, `INSERT INTO` |

---

## Adding Custom Patterns

You can define custom phrase-based (Aho-Corasick) or regex patterns by editing the patterns config file.

### Edit `config/patterns.yaml`

```yaml
patterns:
  # Phone number regex
  - name: phone_number
    regex: "\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b"
    type: PII_STRUCTURAL

  # SSN regex
  - name: ssn
    regex: "\\b\\d{3}-\\d{2}-\\d{4}\\b"
    type: PII_STRUCTURAL

  # Jailbreak phrase (fast phrase search)
  - name: prompt_leak_jailbreak
    phrase: "ignore previous instructions"
    type: INJECTION_ATTEMPT
```

!!! warning "Restart Required"
    Config changes are compiled on container startup. Run the following command after updating `patterns.yaml` to apply changes:
    ```bash
    docker restart instrumentation-sdk-api
    ```

---

## Testing Patterns via REST API

Verify custom pattern behavior instantly via curl:

```bash
curl -X POST http://localhost:8002/v1/pii-injection/scan \
  -H "Content-Type: application/json" \
  -d '{"prompt": "My credit card is 4111-1111-1111-1111"}'
```

Response:
```json
{
  "pii_detected": true,
  "injection_attempt": false
}
```

---

## Next Steps

- [Deterministic Sampling](Deterministic-Sampling.md) - Modulo gates for high-throughput tracking.
- [MiniLM Embeddings](MiniLM-Embeddings.md) - Vector embeddings for semantic search.
