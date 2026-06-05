# gpt2

This is the standard GPT-2 causal language model used for calculating token-level perplexity scores on text inputs when primary provider logprobs are missing.

## Performance Characteristics
- **Size on disk**: ~498 MB (FP32) / ~125 MB (INT8 Quantized)
- **Parameters**: 124M
- **Format**: ONNX Optimized (CPU-only execution)

## Platform Integration
- **Package**: [perplexity](file:///home/btpl-lap-22/live/obs/packages/python/perplexity)
- **Infrastructure Adapter**: [Gpt2ScorerAdapter](file:///home/btpl-lap-22/live/obs/packages/python/perplexity/src/infra/adapters/scorers/gpt2_scorer_adapter.py)
