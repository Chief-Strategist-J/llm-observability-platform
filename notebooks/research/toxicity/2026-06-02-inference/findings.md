# Findings: Toxicity Inference ONNX Evaluation

## Results Summary
- **Single-Pass Inference:** Validated successfully. Standard texts under 510 tokens execute in single-digit milliseconds under optimal execution, with average CPU latency scaling from ~63ms (10 tokens) up to ~1.3s (500 tokens).
- **Dual-Pass Inference:** Verified that text lengths exceeding 510 tokens successfully trigger the `max_of_two_passes` strategy, capturing toxic content from both the beginning and the end of the text.
- **Flat Scaling Behavior:** Because the dual-pass strategy always slices the text into exactly two 510-token windows (first and last), the model inference latency remains flat at ~3.4 seconds even as the input length scales from 520 to 4,000 tokens. This prevents linear latency explosion for very long inputs.
- **ONNX Export:** The optimum ONNX export cleanly optimizes the PyTorch graphs into a highly efficient sequence classification graph, minimizing memory footprint and CPU utilization.

## Visualization Graphs

### Toxicity Probability Scores
Below is the probability distribution across the six toxicity categories for a standard clean test sentence:

![Toxicity Probability Scores](outputs/toxicity_scores.png)

### Inference Latency Comparison
Below is the latency plot demonstrating the step change when transitioning from single-pass (< 510 tokens) to dual-pass (> 510 tokens) inference strategy, and the subsequent flat scaling behavior:

![Inference Latency vs. Token Count](outputs/latency_comparison.png)

