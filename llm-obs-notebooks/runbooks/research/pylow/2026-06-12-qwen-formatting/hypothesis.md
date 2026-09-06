**ADR Reference**: [ADR-005](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/decisions/20260612-005-pylow-qwen-formatting.md)

### Core Hypothesis
If we leverage a sub-1B parameter instruction-tuned causal language model (specifically Qwen2.5-0.5B), we can successfully format raw CLI debugger logs into complex ASCII user interfaces without exceeding the 1GB RAM constraint of local developer machines, thus removing the dependency on costly cloud LLMs.

### Falsification Criteria
The hypothesis is considered falsified if:
1. The memory footprint of the weights during generation exceeds 1024MB.
2. The inference latency for a single debug step summary exceeds 3000ms.
3. The model hallucinates variables not present in the raw log output.
