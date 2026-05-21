# Config Files Reference

All config files live under `packages/python/instrumentation-sdk/`. Most are read once at startup — a container restart is required after changes unless noted otherwise.

---

## `config/model_prices.yaml`

Defines input/output pricing used to auto-compute `cost_usd_micro` for every recorded span.

### Format

```yaml
- model: gpt-4o
  provider: openai
  input_price_per_1m: 5.00
  output_price_per_1m: 15.00
  version: "2025-01-15"
```

| Field | Required | Notes |
|---|---|---|
| `model` | ✅ | Must match the model string returned by the provider |
| `provider` | ✅ | `openai`, `anthropic`, etc. |
| `input_price_per_1m` | ✅ | USD per 1 million input tokens, `>= 0` |
| `output_price_per_1m` | ✅ | USD per 1 million output tokens, `>= 0` |
| `version` | ✅ | Price list date string (stored in span for auditability) |

### Add a New Model

```yaml
- model: gpt-5
  provider: openai
  input_price_per_1m: 10.00
  output_price_per_1m: 30.00
  version: "2026-06-01"
```

CI validates: all required fields present, prices `>= 0`, no duplicate `(model, provider)` pairs.

### After Editing

```bash
docker restart instrumentation-sdk-api
```

### Cost Lookup Behaviour

1. Exact match on `(model, provider)` — used first.
2. Model-only match (any provider) — fallback if provider doesn't match.
3. No match → `cost_usd_micro` is `null` in the span.

---

## `config/patterns.yaml`

Defines PII and injection patterns used by the Aho-Corasick scanner.

### Format

```yaml
patterns:
  - name: email
    regex: "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
    type: PII_STRUCTURAL

  - name: sql_injection
    regex: "(?i)(union|select|insert|update|delete|drop)\\b"
    type: INJECTION_ATTEMPT
```

For phrase-based matching (Aho-Corasick, faster):

```yaml
  - name: jailbreak_ignore
    phrase: "ignore previous instructions"
    type: INJECTION_ATTEMPT
```

| Field | Required | Notes |
|---|---|---|
| `name` | ✅ | Unique identifier — CI rejects duplicates |
| `type` | ✅ | `PII_STRUCTURAL` or `INJECTION_ATTEMPT` |
| `regex` | One of | Compiled with Python `re` — CI validates it compiles |
| `phrase` | One of | Lowercased and loaded into the trie |

### Add a Custom Pattern

```yaml
patterns:
  - name: phone_number
    regex: "\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b"
    type: PII_STRUCTURAL

  - name: ssn
    regex: "\\b\\d{3}-\\d{2}-\\d{4}\\b"
    type: PII_STRUCTURAL

  - name: prompt_leak
    phrase: "repeat the above instructions"
    type: INJECTION_ATTEMPT
```

### After Editing

```bash
docker restart instrumentation-sdk-api
```

### Test Your Pattern Without Restarting

```bash
curl -X POST http://localhost:8002/v1/pii-injection/scan \
  -H "Content-Type: application/json" \
  -d '{"prompt": "My phone is 555-867-5309"}'
```

---

## `build/grafana-datasource.yaml`

Configures Grafana datasources (Tempo for traces, Prometheus for metrics).

```yaml
datasources:
  - name: Tempo
    type: tempo
    access: proxy
    url: http://localhost:3200

  - name: Prometheus
    uid: prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
```

Requires container restart after changes.

---

## `build/prometheus.yml`

Prometheus scrape configuration.

```yaml
global:
  scrape_interval: 5s

scrape_configs:
  - job_name: 'instrumentation-api'
    static_configs:
      - targets: ['localhost:9464']
```

Add additional scrape targets here. Requires container restart.

---

## `build/tempo-config.yaml`

Configures the Tempo trace backend.

```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

storage:
  trace:
    backend: local
    wal:
      path: /tmp/tempo/wal
    local:
      path: /tmp/tempo/blocks
```

Requires container restart after changes.

---

## `build/dashboards/*.json`

Grafana dashboard definitions. **Hot-reloaded every 30 seconds** — no restart needed.

| File | Dashboard |
|---|---|
| `llm-latency-ttft-dashboard.json` | Latency & TTFT percentiles |
| `llm-cost-dashboard.json` | Cost by model and service |
| `llm-error-retry-dashboard.json` | Error rates and retry distribution |
| `llm-security-safety-dashboard.json` | PII and injection rates |

To edit a dashboard in the Grafana UI and save it back:
1. Open the dashboard in Grafana.
2. Make your changes.
3. Click **Dashboard settings → JSON Model**, copy the JSON.
4. Paste into the corresponding `.json` file.
5. The next Grafana poll (within 30 s) picks it up automatically.

---

## CI Validation

The `grafana-config-validate.yml` workflow triggers **only** when one of the 10 watched config files changes. It validates:

| File | Checks |
|---|---|
| `grafana-datasource.yaml` | YAML valid, `name`/`type`/`url` present, Prometheus datasource exists |
| `grafana-dashboard-provider.yaml` | YAML valid, `options.path` present |
| `prometheus.yml` | YAML valid, `scrape_configs` non-empty |
| `tempo-config.yaml` | `server.http_listen_port`, OTLP receivers, storage backend |
| `dashboards/*.json` | JSON valid, `title`/`panels`/`schemaVersion` present, no duplicate UIDs |
| `model_prices.yaml` | Non-empty, all required fields, prices `>= 0`, no duplicate pairs |
| `patterns.yaml` | All required fields, valid `type`, no duplicate names, regex compiles |

CI runs in ~60 seconds, no Docker required.

---

## Summary — Restart Required?

| Config file | Restart required? |
|---|---|
| `config/model_prices.yaml` | ✅ Yes |
| `config/patterns.yaml` | ✅ Yes |
| `build/grafana-datasource.yaml` | ✅ Yes |
| `build/grafana-dashboard-provider.yaml` | ✅ Yes |
| `build/prometheus.yml` | ✅ Yes |
| `build/tempo-config.yaml` | ✅ Yes |
| `build/dashboards/*.json` | ❌ No — hot-reloaded every 30 s |
