# Findings: Toxicity Inference ONNX Evaluation

## Results Summary
- **Single-Pass Inference:** Validated successfully. Standard texts under 510 tokens execute in single-digit milliseconds.
- **Dual-Pass Inference:** Verified that text lengths exceeding 510 tokens successfully trigger the `max_of_two_passes` strategy, capturing toxic content from both the beginning and the end of the text.
- **ONNX Export:** The optimum ONNX export cleanly optimizes the PyTorch graphs into a highly efficient sequence classification graph, minimizing memory footprint and CPU utilization.
