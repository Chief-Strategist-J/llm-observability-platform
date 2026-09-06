# Hypothesis: Toxicity Inference ONNX Speed and Accuracy Verification

## Objective
Verify the performance, tokenization behavior, and output scores of the decoupled `toxicity-worker` using the `unitary/toxic-bert` model exported to ONNX Runtime.

## Hypotheses
1. ONNX Runtime inference latency on CPU for a standard text (under 510 tokens) will be well within the P95 SLO of 200ms.
2. The dual-pass token window logic correctly captures toxicity at the end of a long text (>510 tokens) that would otherwise be truncated.
3. FastAPI rest endpoints provide correct header propagation and return matching predictions compared to raw adapter scoring.
