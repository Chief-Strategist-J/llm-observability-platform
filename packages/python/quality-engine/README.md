# Quality Engine

LLM Observability Quality Engine package.

## Introduction

This service aggregates model evaluation metrics (coherence, faithfulness, toxicity, and perplexity) into a single composite quality score. It implements dynamic weight renormalization to handle missing inputs and triggers console alerts if all sub-metrics are null.

## API Documentation

- `GET /health` - Health check endpoint.
- `POST /v1/score/composite` - Calculate composite score.

## Development

Install development dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```
