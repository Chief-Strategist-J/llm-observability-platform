# Changelog — Quality Engine OpenAPI Contract

## [1.0.0] — 2026-06-01

- Initial contract: POST /v1/score/composite, GET /health
- Computes composite quality score from coherence, faithfulness, toxicity, and perplexity scores.
- Dynamic renormalization of weights when individual scores are null.
- Triggers alert when all inputs are null.
