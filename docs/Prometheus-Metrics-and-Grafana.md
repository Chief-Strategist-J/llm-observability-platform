# Prometheus Metrics & Grafana

The SDK ships four pre-built Grafana dashboards and a Prometheus scrape pipeline. Everything is auto-provisioned inside the all-in-one container — no manual wiring needed.

---

## Quick Start

```bash
# Start the stack (API + Grafana + Prometheus + Tempo)
llm-observe start

# Open Grafana
open http://localhost:3002
# Default credentials: admin / admin
```

Navigate to **Dashboards → LLM Observability** to see all four dashboards.

---

## Dashboards

### 1. LLM Latency & TTFT

`http://localhost:3002/d/llm-latency-ttft-dashboard`

| Panel | What it shows |
|---|---|
| Latency Percentiles (p50 / p95 / p99) | End-to-end call latency by model |
| TTFT Percentiles (p50 / p95 / p99) | Time to first token for streaming calls |
| Avg Latency vs Avg TTFT | Bar chart comparison per model |

### 2. LLM Cost Dashboard

`http://localhost:3002/d/llm-cost-dashboard`

| Panel | What it shows |
|---|---|
| Cumulative Cost Over Time | USD cost per service + model over time |
| Cost Distribution by Model | Donut chart — which models cost the most |
| Cost Distribution by Service | Horizontal bar chart per service |

### 3. LLM Error & Retry Dashboard

`http://localhost:3002/d/llm-error-retry-dashboard`

| Panel | What it shows |
|---|---|
| Success vs Error Rate | Stacked time series |
| Finish Reason Distribution | Bar chart: `stop`, `length`, `content_filter`, etc. |
| Retry Rate (%) | Gauge showing % of spans with retries |

### 4. LLM Security & Safety Dashboard

`http://localhost:3002/d/llm-security-safety-dashboard`

| Panel | What it shows |
|---|---|
| PII Detection Rate | Detections/sec by service |
| Prompt Injection Attempts Rate | Attempts/sec by service |
| Total Security Violations | Cumulative PII + injection count |
| Violations Over Time | Stacked bar chart |

---

## Initialize the Metrics Pipeline

The pipeline starts automatically when the container starts. To initialize it manually (e.g. from your own app):

```bash
curl -X POST http://localhost:8002/v1/metrics/init \
  -H "Content-Type: application/json" \
  -d '{"port": 9464}'
```

Response:
```json
{"initialized": true, "message": "Metrics pipeline initialized"}
```

Check health:
```bash
curl http://localhost:8002/v1/metrics/health
```
```json
{"initialized": true, "message": "Metrics pipeline is active"}
```

---

## Record Metrics Manually

### Single Span

```bash
curl -X POST http://localhost:8002/v1/metrics/record \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "provider": "openai",
    "service_name": "chat-api",
    "prompt_tokens": 150,
    "completion_tokens": 80,
    "latency_ms_total": 420,
    "latency_ms_ttft": 95,
    "finish_reason": "stop",
    "status": "success",
    "pii_detected": false,
    "injection_attempt": false,
    "retry_count": 0
  }'
```

Response:
```json
{
  "recorded": true,
  "cost_usd_micro": 1950,
  "price_version": "2025-01-15"
}
```

Cost is auto-computed from `config/model_prices.yaml`. If the model isn't in the price list, `cost_usd_micro` is `null`.

### Batch Spans

```bash
curl -X POST http://localhost:8002/v1/metrics/record-batch \
  -H "Content-Type: application/json" \
  -d '{
    "spans": [
      {
        "model": "gpt-4o", "provider": "openai", "service_name": "chat-api",
        "prompt_tokens": 100, "completion_tokens": 50,
        "latency_ms_total": 300, "status": "success"
      },
      {
        "model": "gpt-3.5-turbo", "provider": "openai", "service_name": "summarizer",
        "prompt_tokens": 2000, "completion_tokens": 400,
        "latency_ms_total": 1200, "status": "success"
      }
    ]
  }'
```

Response:
```json
{"recorded_count": 2}
```

---

## Prometheus Metrics Reference

Scraped from `http://localhost:9464/metrics` every 5 seconds.

| Metric | Type | Labels |
|---|---|---|
| `llm_tokens_total` | Counter | `model`, `provider`, `service_name`, `token_type` |
| `llm_cost_usd_micro_total` | Counter | `model`, `provider`, `service_name` |
| `llm_latency_ms_total` | Histogram | `model`, `provider`, `service_name` |
| `llm_latency_ms_ttft` | Histogram | `model`, `provider`, `service_name` |
| `llm_pii_detected_total` | Counter | `service_name` |
| `llm_injection_attempts_total` | Counter | `service_name` |
| `llm_finish_reason_total` | Counter | `model`, `provider`, `service_name`, `finish_reason` |
| `llm_spans_total` | Counter | `model`, `provider`, `service_name`, `status`, `has_retries` |

---

## Add a New Model Price

Edit `config/model_prices.yaml`:

```yaml
- model: gpt-5
  provider: openai
  input_price_per_1m: 10.00
  output_price_per_1m: 30.00
  version: "2026-01-01"
```

Then restart:
```bash
docker restart instrumentation-sdk-api
```

CI validates that all required fields are present, prices are `>= 0`, and no `(model, provider)` pair is duplicated.

---

## Dashboard Hot-Reload

Grafana polls `build/dashboards/*.json` every **30 seconds**. Edit a dashboard JSON file and it updates live — no restart needed.

All other infra configs (`grafana-datasource.yaml`, `prometheus.yml`, `tempo-config.yaml`) require a container restart.

---

## Next: [REST Management API](REST-Management-API)
