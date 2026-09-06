# ADR-002 — Perplexity Scorer Dual-Path Routing and Failure-First Fallbacks

| Field       | Value                                                             |
|-------------|-------------------------------------------------------------------|
| **ID**      | 002                                                               |
| **Date**    | 2026-06-03                                                        |
| **Status**  | accepted                                                          |
| **Deciders**| LLM Observability Platform Team                                   |
| **Package** | `packages/python/perplexity`                                      |

---

## Context

Perplexity is a critical metric for LLM observability, detecting text distribution drift, potential hallucinations, and adversarial inputs. Calculating perplexity requires measuring the probability distribution of a text sequence.

Historically, this required running model inference on a causal language model (e.g. GPT-2) for every scored text, which introduces significant computational cost:
1. **CPU Overhead**: Model inference is CPU-bound and slow on standard container runtimes.
2. **Latency SLO**: The platform has a strict P95 timeout SLA of 150ms. Running full sequence inference on texts longer than a few hundred tokens on CPU routinely violates this.
3. **Provider Data**: Some LLM providers (e.g., OpenAI API) optionally return token-level logprobs directly in their response payload, rendering local inference redundant.

### Driving Forces
- Minimize inference cost (CPU and memory) in production.
- Adhere to the strict 150ms timeout SLO.
- Maintain a reliable metric pipeline even when provider logprobs are not available.
- Prevent container crashes due to OOM under resource constraints.

---

## Decision

Implement a **dual-path scoring architecture** inside the `perplexity` microservice. This decouples the scoring interface via Hexagonal Ports (e.g. `Gpt2ScorerPort`) and routes the incoming payload dynamically based on the presence of provider-supplied token logprobs.

```
                  POST /perplexity
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
    [logprobs present]       [logprobs absent]
             │                       │
      (Provider Path)         (Fallback Path)
    O(1) Math on logs        GPT-2 ONNX on CPU
    Latency: < 1ms          Latency: O(N) (Slow)
```

### The Two Paths
1. **Provider Path (A)**: If `logprobs` is present in the request body, extract the logprobs sequence and compute:
   $$\text{Perplexity} = \exp\left(-\frac{1}{N}\sum_{i=1}^{N} \log P(x_i)\right)$$
   This has $O(1)$ computation cost, zero inference model footprint, and < 1ms latency.
2. **Fallback Path (B)**: If `logprobs` is absent, invoke the `Gpt2OnnxAdapter` to tokenize the text and run a local GPT-2 (124M parameter) ONNX model on CPU. Compute token count and loss in a single forward pass, returning perplexity as $\exp(\text{loss})$.

---

## Failure-First System Building (FFSB) Analysis

Applying the platform's brutal failure-first framework (`ffsb.md`), we identify the following key failure modes:

### Mode 1: Slow Not Down (FastAPI Thread Starvation)
- **Symptom**: Under concurrent load, the service becomes unresponsive (SLO violated), but Kubernetes health checks remain green (`/health` returns `200` because it does not trigger inference).
- **Trigger**: High concurrent traffic without provider logprobs triggers the CPU-bound ONNX model fallback. It takes ~500ms-2.5s on 1 CPU core for sequences of 500-1024 tokens. This starves the FastAPI ASGI thread pool.
- **Recovery/Prevention**:
  - Restrict input sequence length in the adapter to `truncation=True, max_length=520` or `1024` tokens.
  - Implement client-side timeouts (150ms SLO) to prevent thread block cascade.
  - Configure resource limits (`CPU_REQUEST: 500m`, `CPU_LIMIT: 1000m`).

### Mode 2: Correct Response, Wrong Data (Logprobs Base Mismatch)
- **Symptom**: The calculated perplexity score is mathematically incorrect (e.g. yielding values too low or infinity) due to an incorrect log probability representation.
- **Trigger**: Providers return logprobs in different mathematical bases (base-e $ln$, base-10 $\log_{10}$, base-2 $\log_2$). If the adapter blindly calculates $e^{-\text{mean}(\log P)}$, a base-10 logprob input will produce incorrect perplexity.
- **Recovery/Prevention**:
  - Implement range bounding checks: logprobs should generally sit in $[-\infty, 0.0]$.
  - Add validation in `extract_token_logprobs` to ensure a consistent list shape.

### Mode 3: Works Until Conditions Met (OOM Termination)
- **Symptom**: The container crashes instantly with `OOMKilled` when a fallback request arrives.
- **Trigger**: The service uses a default container memory limit of 512Mi. A standard FP32 GPT-2 124M model file is ~498MB. Loading this file, plus the ONNX Runtime engine, Python runtime, and FastAPI framework, requires ~750MB-1GB of memory. It will reliably crash under the 512Mi constraint.
- **Recovery/Prevention**:
  - Document that the fallback path *requires* increasing container memory limits to `1Gi` (minimum) in production, or exporting the model in INT8 quantized format (~125MB) to run comfortably within a 256Mi/512Mi memory budget.

### Mode 4: Cascading Failure (Collector Blocks)
- **Symptom**: When perplexity service slows down or becomes unavailable, the main observability collector stops collecting all LLM traces.
- **Trigger**: The collector calls `/perplexity` synchronously.
- **Recovery/Prevention**:
  - The collector must invoke perplexity scoring asynchronously or inside a non-blocking queue. If perplexity times out or fails, skip the metric calculation and return a warning/skip flag rather than throwing a span collection error.

---

## Consequences

### Positive
- **Zero-cost inference**: >90% of requests use the provider logprobs path in production, saving massive CPU cycles.
- **Fully fallback-capable**: Retains observability for custom models or providers that don't output logprobs.
- **Hexagonal cleanliness**: Swapping the concrete model (e.g., to Llama-3-ONNX or quantized GPT-2) only requires changing the adapter, keeping HTTP routing untouched.

### Negative / Trade-offs
- **High memory footprint**: Fallback model takes ~500MB of RAM, causing severe OOM risks on default 512Mi limits if quantization is not enabled.
- **Model cache startup latency**: The first fallback request experiences a cold start of 2-5 seconds while the model is loaded into the ONNX Runtime session.

---

## Alternatives Considered

### A — Direct ONNX Inference for All Requests
Calculate perplexity on GPT-2 ONNX for all incoming requests, ignoring provider logprobs.
- **Rejected because**: Incurs huge CPU costs and violates the 150ms timeout SLO.

### B — Reject Requests Lacking Provider Logprobs
Do not calculate perplexity unless the user/provider passes logprobs.
- **Rejected because**: Observability suffers for custom LLMs and platforms where logprobs are unavailable.

---

## References
- [FFSB Checklist](file:///home/btpl-lap-07/prod/llm-observability-platform/.windsurf/rules/runbook/ffsb.md)
- [ADR Guidelines](file:///home/btpl-lap-07/prod/llm-observability-platform/.windsurf/rules/runbook/adr.md)
- `packages/python/perplexity/src/infra/adapters/gpt2/gpt2_onnx_adapter.py`
- `packages/python/perplexity/src/api/rest/v1/handlers/score_inference.py`
