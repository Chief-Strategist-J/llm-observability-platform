# Quality Engine

LLM Observability Quality Engine package.

## Introduction

This service aggregates model evaluation metrics (coherence, faithfulness, toxicity, and perplexity) into a single composite quality score. It implements dynamic weight renormalization to handle missing inputs and triggers console alerts if all sub-metrics are null.

If sub-metrics are not provided directly in the request payload, the quality engine can dynamically fetch them by querying the downstream sub-scorer microservices if they are configured in the environment.

## Environment Variables

| Variable | Description | Default |
| --- | --- | --- |
| `COHERENCE_SERVICE_URL` | Endpoint of the Semantic Coherence Scorer service | `http://localhost:8005` |
| `FAITHFULNESS_SERVICE_URL` | Endpoint of the Faithfulness Scorer service | `http://localhost:8006` |
| `TOXICITY_SERVICE_URL` | Endpoint of the Toxicity Scorer service | `http://localhost:8007` |
| `PERPLEXITY_SERVICE_URL` | Endpoint of the Perplexity Scorer service | `http://localhost:8007` |

## API Documentation

- `GET /health` - Health check endpoint.
- `POST /v1/score/composite` - Calculate composite score.

### API Request Schema

The request payload accepts both pre-calculated scores and raw parameters to compute them on-the-fly:

- `trace_id` (string, required)
- `span_id` (string, required)
- `coherence_score` (float, optional)
- `faithfulness_score` (float, optional)
- `toxicity_score` (float, optional)
- `perplexity` (float, optional)
- `perplexity_baseline` (float, default: `2.0`)
- `use_literal_formula` (boolean, default: `false`)
- `prompt_type` (string, optional)
- `pii_detected` (boolean, optional)
- `prompt_embedding` (array of floats, optional)
- `response_embedding` (array of floats, optional)
- `response_text` (string, optional)
- `completion_tokens` (integer, optional)
- `rag_context` (string, optional)
- `finish_reason` (string, optional)
- `token_logprobs` (array of floats, optional)

## Development

Install development dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```
