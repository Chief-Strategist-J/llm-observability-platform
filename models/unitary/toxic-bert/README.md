# unitary/toxic-bert

This BERT model is trained to detect multi-label toxicity across six categories:
- toxicity
- severe_toxicity
- obscene
- threat
- insult
- identity_hate

## Performance Characteristics
- **Size on disk**: ~410 MB
- **Parameters**: 110M
- **Format**: ONNX Optimized (CPU-only execution)

## Platform Integration
- **Package**: [toxicity](file:///home/btpl-lap-22/live/obs/packages/python/toxicity)
- **Infrastructure Adapter**: [ToxicityScorerAdapter](file:///home/btpl-lap-22/live/obs/packages/python/toxicity/src/infra/adapters/scorers/toxicity_scorer_adapter.py)
