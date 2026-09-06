# ADR 0001: ONNX Runtime CPU Inference with Dual-Pass Long-Text Strategy

| Field | Value |
| --- | --- |
| **ADR ID** | `ADR-PYTHON-TOXICITY-0001` |
| **Title** | Use ONNX Runtime on CPU with Dual-Pass Chunking for Toxicity Scoring |
| **Status** | **Accepted** |
| **Date** | 2026-05-29 |
| **Scope** | `packages/python/toxicity` — inference engine, long-text handling, token limits |

---

## 1. Context & Problem Statement

How should the toxicity service classify multi-label toxicity for LLM response texts of arbitrary length, given:

- `unitary/toxic-bert` (BERT-base) has a hard 512-token input limit.
- LLM responses routinely exceed 512 tokens — a single chat turn in a coding assistant can be 2,000+ tokens.
- The service must run on **CPU-only** infrastructure (no GPU available in the target deployment).
- Inference must complete in under **500 ms p99** to avoid blocking the span-enrichment pipeline.
- The model must be **portable** — no CUDA/ROCm driver dependency.

---

## 2. Failure Modes We Are Solving

| ID | Symptom | Root Cause | Severity |
|---|---|---|---|
| **FM-01** | Long responses silently truncated at 512 tokens | BERT tokenizer hard limit | HIGH — toxic content at end of response is missed |
| **FM-02** | GPU dependency makes deployment fragile | PyTorch CUDA requires driver pinning | HIGH — breaks on CPU-only nodes |
| **FM-03** | Full PyTorch inference too slow on CPU | No JIT optimization for CPU path | MEDIUM — p99 > 2s on commodity CPU |
| **FM-04** | Model loaded fresh per request | No lazy/cached model loading | CRITICAL — 8–15s startup per request |

---

## 3. Decision Drivers

- **D1**: Must correctly score responses longer than 512 tokens — missing tail toxicity is a safety gap.
- **D2**: Must run on CPU without GPU drivers.
- **D3**: Inference latency must stay under 500ms p99 on commodity CPU (4 vCPU, 8 GB RAM).
- **D4**: Model must load once at process start, not per request.
- **D5**: Must produce per-label scores (toxicity, severe_toxicity, obscene, threat, insult, identity_hate).

---

## 4. Options Considered

### Option A — Full PyTorch, truncate at 512 tokens *(rejected)*
- Solves: D5 (per-label scores).
- Does not solve: FM-01 (truncation), FM-02 (GPU dep), FM-03 (CPU speed).
- **Eliminated**: truncation is a safety gap; FM-01 is non-negotiable.

### Option B — ONNX Runtime export of `unitary/toxic-bert` via `optimum` *(chosen)*
- Solves: FM-02 (CPU-only via `onnxruntime` CPU provider), FM-03 (ONNX graph optimised for CPU, ~3–4× faster than PyTorch CPU), FM-04 (`cached_property` loads model once).
- Does not solve FM-01 alone — requires chunking strategy on top.

### Option C — HuggingFace `pipeline` with sliding window *(rejected)*
- Solves: FM-01, FM-05.
- Does not solve: FM-02 (pipeline uses full PyTorch), FM-03.
- **Eliminated**: GPU dependency and CPU latency too high.

### Option D — External toxicity API (Perspective API) *(rejected)*
- Solves: FM-01, FM-03, FM-04.
- Creates: external network call on every LLM span (latency + availability), data-privacy concern (sending customer text to Google), quota limits.
- **Eliminated**: privacy and availability constraints unacceptable.

---

## 5. Decision Outcome

**Chosen: Option B (ONNX Runtime) + dual-pass chunking strategy.**

For texts with more than 510 tokens:
1. Score `tokens[:510]` (first 510 tokens, padded with `[CLS]`/`[SEP]`).
2. Score `tokens[-510:]` (last 510 tokens).
3. Take element-wise `max()` across all six labels.
4. Set `long_response_strategy = "max_of_two_passes"` in the response.

**Why max-of-two-passes over sliding-window average:**
- Average dilutes a localised toxic segment in a long benign response — a 10-token toxic burst in 2,000 tokens scores near 0.0 on average.
- Max-of-two preserves worst-case detection; a false positive is preferable to a false negative in a safety system.

---

## 6. Failure Modes Created

| ID | Name | Symptom | Detection | Threshold | Recovery | Prevention |
|---|---|---|---|---|---|---|
| **FM-NEW-01** | Middle-segment blind spot | Content in tokens 511–(N-511) is unscored in responses > 1,020 tokens | Monitor `long_response_strategy="max_of_two_passes"` + manual QA | If flagged rate drops unexpectedly | Extend to 3-pass for very long responses | Log response length histogram per scored span |
| **FM-NEW-02** | ONNX model file mismatch after `optimum` upgrade | Inference returns wrong logit ordering | Smoke test on startup with known fixture | Any production test failure | Re-export model (`export=True`) on next deploy | Pin `optimum` version in `pyproject.toml` |
| **FM-NEW-03** | Warmup delay on first request | Cold container: first request takes 8–15s | Health check reports `ok` before warmup completes | Startup latency > 5s | Warmup called in `lifespan()` before container marked ready | `HEALTHCHECK --start-period=30s` in Dockerfile |

---

## 7. Consequences

### Positive
- CPU-only inference at ~150–250ms p99 on 4-vCPU node.
- Zero GPU driver dependency — deploys on any standard Python container.
- Model loaded once via `cached_property` — zero per-request overhead after warmup.
- Worst-case toxicity preserved in long responses — safety gap closed.

### Negative
- Middle segment of responses > 1,020 tokens is unscored (FM-NEW-01 — documented, accepted).
- ONNX export must be re-run after `optimum` or `transformers` major upgrades.
- `torch` remains a dependency (required for tensor ops) — adds ~1.5 GB to container image.

---

## 8. Review Trigger

Revisit this ADR if:
- Average LLM response length exceeds 1,500 tokens (middle-blind-spot becomes statistically significant).
- A GPU node becomes available in the deployment cluster (switch to CUDA ONNX provider for 10× speedup).
- `optimum` releases a stable ONNX-CPU streaming inference API (enables true sliding window without 2× inference cost).
