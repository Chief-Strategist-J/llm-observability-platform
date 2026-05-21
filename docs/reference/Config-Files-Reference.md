# Config Files Reference

Most configuration settings live under `packages/python/instrumentation-sdk/`. Most files are parsed at boot time; changing them requires a container restart.

---

## Configuration File Tree

```
packages/python/instrumentation-sdk/
├── config/
│   ├── model_prices.yaml      <── Price definitions for cost calculation
│   └── patterns.yaml          <── PII and injection scanner patterns
└── build/
    ├── grafana-datasource.yaml <── Grafana database connections
    ├── prometheus.yml          <── Scraper target addresses
    ├── tempo-config.yaml       <── Jaeger/Tempo OTLP endpoints
    └── dashboards/             <── Dashboard JSON specifications
```

---

## 1. `config/model_prices.yaml`

Contains token pricing metrics used to compute `cost_usd_micro` fields on spans.

### Schema

```yaml
- model: gpt-4o
  provider: openai
  input_price_per_1m: 5.00
  output_price_per_1m: 15.00
  version: "2025-01-15"
```

| Parameter | Required | Purpose / Validation |
|---|:---:|---|
| `model` | ✅ | Model identifier string from provider response |
| `provider` | ✅ | `openai`, `anthropic`, etc. |
| `input_price_per_1m` | ✅ | USD per 1,000,000 input tokens (`>= 0`) |
| `output_price_per_1m` | ✅ | USD per 1,000,000 output tokens (`>= 0`) |
| `version` | ✅ | String representing configuration version date |

---

## 2. `config/patterns.yaml`

Contains matching targets used by Aho-Corasick prefix matches or Python `re` compilers.

### Schema

```yaml
patterns:
  # Regex-based match
  - name: email
    regex: "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
    type: PII_STRUCTURAL

  # Phrase-based match
  - name: jailbreak_ignore
    phrase: "ignore previous instructions"
    type: INJECTION_ATTEMPT
```

| Parameter | Required | Purpose / Validation |
|---|:---:|---|
| `name` | ✅ | Unique name identifier |
| `type` | ✅ | Must be either `PII_STRUCTURAL` or `INJECTION_ATTEMPT` |
| `regex` | ⚠️ | Regex string (must compile with python standard `re` module) |
| `phrase` | ⚠️ | Raw phrase match (case-insensitive trie matching) |

---

## 3. Infrastructure Configs

### `build/grafana-datasource.yaml`
Configures connections linking Grafana to Tempo and Prometheus:
```yaml
datasources:
  - name: Tempo
    type: tempo
    url: http://localhost:3200
  - name: Prometheus
    type: prometheus
    url: http://localhost:9090
    isDefault: true
```

### `build/prometheus.yml`
Instructs Prometheus where to scrape telemetry counters:
```yaml
scrape_configs:
  - job_name: 'instrumentation-api'
    scrape_interval: 5s
    static_configs:
      - targets: ['localhost:9464']
```

---

## CI Verification Checks

When pushing commits, the configuration validator runs tests against all yaml/json files:

| Target File | Validation Metrics |
|---|---|
| `model_prices.yaml` | Non-empty, no duplicate `(model, provider)` keys, all values `>= 0`. |
| `patterns.yaml` | Valid regex structures, unique pattern names, type checks. |
| `dashboards/*.json` | Valid JSON formatting, no duplicate panel UIDs. |

---

## Restart Requirements Matrix

| File Target | Restart Required on Change? |
|---|:---:|
| `config/model_prices.yaml` | ✅ Yes |
| `config/patterns.yaml` | ✅ Yes |
| `build/grafana-datasource.yaml` | ✅ Yes |
| `build/prometheus.yml` | ✅ Yes |
| `build/tempo-config.yaml` | ✅ Yes |
| `build/dashboards/*.json` | ❌ No (hot-reloaded every 30s) |
