# Perplexity Scorer

Layer 3 perplexity scoring microservice — Score 4 in the composite quality index.

## Quick Start

```bash
pip install -e ".[dev]"
SKIP_CONSOLE_EXPORTER=true SKIP_OTLP_EXPORTER=true pytest tests/ -q
```

## Algorithm

```
Primary:   Provider logprobs → sum(token_logprobs) / token_count → exp(-avg) = perplexity
Fallback:  GPT-2 124M ONNX on CPU (~25ms / 200-token response)
Formula:   perplexity = exp(-1/N × Σ log P(token_i | token_{<i}))
```

## Skip Conditions

| Condition | skip_reason |
|---|---|
| `completion_tokens < 10` | `completion_tokens_too_few` |
| `finish_reason == "content_filter"` | `finish_reason_blocked` |
| No provider logprobs AND GPT-2 unavailable | `scorer_unavailable` |

## Baselines

| prompt_type | Expected perplexity |
|---|---|
| chat | 15–35 |
| code | 8–20 |
| rag | 12–28 |
| classification | 6–15 |

`HIGH_PERPLEXITY` flag is raised when `perplexity > 3 × baseline_high`.

## Composite Weight

| State | w_perplexity | contribution |
|---|---|---|
| perplexity not null | 0.10 | `1/log(perplexity)` normalized to [0,1] |
| perplexity null | 0.00 | other weights renormalized externally |

## API

```
POST /v1/score/perplexity
GET  /health
```

## Architecture

```
domain (types, rules, service)   ← zero infra imports
      ↓ ports (Protocol)
infra (provider_logprobs_adapter, gpt2_onnx_adapter)
      ↓
api   (FastAPI handler → service)
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GPT2_MODEL_PATH` | `gpt2` | HuggingFace model path for GPT-2 ONNX |
| `SKIP_CONSOLE_EXPORTER` | `false` | Suppress OTel console output |
| `SKIP_OTLP_EXPORTER` | `true` | Skip OTLP exporter |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP endpoint |
| `DEPLOYMENT_ENV` | `dev` | OTel resource attribute |

## Docker

```bash
docker run -p 8007:8007 chiefj/perplexity:latest
```
