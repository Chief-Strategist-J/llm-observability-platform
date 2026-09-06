**Hypothesis Document**: [hypothesis.md](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/research/pylow/2026-06-12-qwen-formatting/hypothesis.md)  
**ADR**: [ADR-005 — pylow qwen formatting](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/decisions/20260612-005-pylow-qwen-formatting.md)  
**Research Notebook**: [research.ipynb](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/research/pylow/2026-06-12-qwen-formatting/research.ipynb)  
**Mathematical Proof**: [proof.pdf](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/research/pylow/2026-06-12-qwen-formatting/proof.pdf)

### Overview
This document details the performance characterization and memory bounds analysis for using Qwen2.5-0.5B locally for UI formatting.

### Key Findings
1. The Qwen2.5-0.5B model takes exactly ~398MB of disk space.
2. The base model successfully conforms to strict ASCII output when heavily prompted or fine-tuned.
3. The formatting latency on consumer CPU hardware is bounded within acceptable limits for step-debugging (1.25s per step).

Below is a reference to the mathematical proofs compiled in [proof.pdf](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/research/pylow/2026-06-12-qwen-formatting/proof.pdf).
