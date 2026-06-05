# cross-encoder/nli-deberta-v3-base

This is a Natural Language Inference (NLI) model based on DeBERTa-v3-base. It classifies sentence-pairs into three classes:
- **Entailment** (class 1)
- **Neutral** (class 2)
- **Contradiction** (class 0)

## Performance Characteristics
- **Size on disk**: ~370 MB
- **Parameters**: 186M
- **Average Latency**: 
  - CPU: ~26 ms (batch size = 8)
  - GPU: ~5.5 ms (batch size = 8)

## Platform Integration
- **Package**: [nli-worker](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker)
- **Clean Architecture Port**: [NliScorerPort](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker/src/core/domain/ports/nli_scorer_port.py)
- **Infrastructure Adapter**: [NliScorerAdapter](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker/src/infra/adapters/nli_scorer_adapter.py)
