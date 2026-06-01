# Changelog — Perplexity Scorer OpenAPI Contract

## [1.0.0] — 2026-06-01

- Initial contract: POST /v1/score/perplexity, GET /health
- Primary path: provider logprobs (token_logprobs array)
- Fallback path: GPT-2 ONNX inference
- skip_reason enum: completion_tokens_too_few, finish_reason_blocked, scorer_unavailable
- high_perplexity_flag when perplexity > 3 × prompt_type baseline
- w_perplexity: 0.10 (active) / 0.00 (skipped)
