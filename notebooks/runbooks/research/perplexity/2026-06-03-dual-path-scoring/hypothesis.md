# Hypothesis: Perplexity Dual-Path Scorer Evaluation

## Objective
Verify the correctness, latency profiles, memory footprints, and token constraints of the dual-path perplexity microservice under simulated and empirical workloads.

## Hypotheses
1. **Mathematical Equivalence**: Calculating perplexity directly from provider-supplied token logprobs:
   $$\text{Perplexity} = \exp\left(-\frac{1}{N}\sum_{i=1}^N \log P(x_i)\right)$$
   produces identical scoring outputs to running GPT-2 ONNX fallback loss scoring on the same token sequence, assuming identical vocabulary and tokenizer token alignment.
2. **Latency Discrepancy ($O(1)$ vs $O(N)$)**:
   - The *Provider Path* (direct logprobs math) will remain sub-millisecond (< 1ms) regardless of the sequence length.
   - The *Fallback Path* (GPT-2 ONNX CPU inference) will show a linear dependency on sequence length, with latencies scaling from ~100ms (for short texts) to > 1500ms (for 1024 tokens) on 1 CPU core, routinely violating the 150ms P95 SLO for sequences longer than 128 tokens.
3. **Works Until Conditions Met (OOM Limit)**:
   - Loading the FP32 GPT-2 model session via `optimum.onnxruntime.ORTModelForCausalLM` will allocate > 500MB of RAM, causing immediate container crash under a strict 512Mi memory limit.
   - Enabling INT8 dynamic quantization or increasing the container memory request limit to 1Gi will fully mitigate this failure mode, ensuring stable operation.
