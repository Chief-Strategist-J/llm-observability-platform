# Quality Engine

LLM Observability Quality Engine package.

## Introduction

This service aggregates model evaluation metrics (coherence, faithfulness, toxicity, and perplexity) into a single composite quality score. It implements dynamic weight renormalization to handle missing inputs and triggers console alerts if all sub-metrics are null.

If sub-metrics are not provided directly in the request payload, the quality engine can dynamically fetch them by querying the downstream sub-scorer microservices if they are configured in the environment.

## Business Decision Tree

```
[quality-ST-01 | Request Received]
   |
   +-- [quality-IN-01 | CompositeScoreInput (trace_id, span_id, scores, text attributes)]
       |
       +-- [quality-DC-01 | Pre-calculated scores provided?]
           |-- [yes | Use provided values for coherence, faithfulness, toxicity, perplexity]
           |-- [no  | ScorerClientPort configured?]
           |          |-- [yes | Fetch missing scores dynamically from downstream microservices]
           |          `-- [no  | Retain null for missing scores]
           |
           `-- [quality-PR-01 | Renormalize weights for non-null metrics]
               |   Base weights: coherence=0.30, faithfulness=0.40, toxicity=0.20, perplexity=0.10
               |   normalized_weight = weight / sum(active_weights)
               |
               +-- [quality-DC-02 | Are all active scores null?]
                   |-- [yes | Trigger alert: 'scoring pipeline is broken' (trace_id, span_id)]
                   |          quality_skipped_reason = 'all_scores_null'
                   |          composite_score = null
                   |-- [no  | Calculate composite_score = Σ (normalized_weight * raw_contribution)]
                   |
                   `-- [quality-OUT-01 | Return CompositeScoreResult]
```

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

## CI / CD

The pipeline (`quality-engine-test.yml`) is run automatically on GitHub Actions on pushes and pull requests targeting branches that match `main` or `feature/**` when changes are made inside the `packages/python/quality-engine/` directory. It executes the test suite.

