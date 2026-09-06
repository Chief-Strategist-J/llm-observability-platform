# ADR-008 — Phase 3 Perplexity, Quality Baselines, and Degradation Alerts

| Field       | Value                                                             |
|-------------|-------------------------------------------------------------------|
| **ID**      | 008                                                               |
| **Date**    | 2026-06-15                                                        |
| **Status**  | accepted                                                          |
| **Deciders**| LLM Observability Platform Team                                   |
| **Package** | `packages/python/quality-engine`, `packages/python/alert-engine`, `packages/python/perplexity` |

---

## Context

Following the success of Phase 2, we needed to deliver Phase 3 capabilities:
1. **Perplexity Scoring**: Load and deploy a perplexity-worker container utilizing GPT-2 ONNX at startup. This worker must score LLM responses using two paths: `provider_logprobs` (when token logprobs are available) and `gpt2_onnx` (fallback inference for provider API responses lacking logprobs).
2. **Quality aggregation integration**: Incorporate perplexity scoring as the 4th active dimension in composite quality score calculations, using a renormalized weight allocation:
   - Coherence: 0.25 (reduced from 0.30)
   - Faithfulness: 0.35 (reduced from 0.40)
   - Toxicity: 0.15 (reduced from 0.20)
   - Perplexity: 0.10 (increased from 0.00)
3. **Dynamic thresholding**: Detect high-perplexity responses if raw perplexity is greater than 3 × the prompt type's baseline.
4. **Baselines Management**: Read default p50 baselines from a YAML file (`perplexity_baselines.yaml`) and hot-reload changes on the fly using a watchdog thread.
5. **Quality Degradation Alerts**: Detect average quality drops (below 90% of baseline over a 1-hour window) and publish them to Kafka (`alerts.quality.degradation`).
6. **Cold Start Safeguard**: Prevent spamming Slack during cold-starts when baselines do not exist or are sparse. 

---

## Decision

We implemented the following architecture and design choices:

- **Dual-Path Perplexity Service**: The perplexity worker implements `POST /v1/score/perplexity` routing queries either to a provider-native token probability decoder or local GPT-2 inference.
- **Dynamic Renormalization (4-weight)**: Modified `composite_scorer.py` in `quality-engine` to dynamically integrate perplexity. Normalization converts raw perplexity to a [0, 1] quality contribution using the formula: `clamp(1 - perplexity/200, 0, 1)`. If perplexity or other metrics are absent (e.g. timeout), weights renormalize automatically to maintain backwards-compatibility.
- **Asynchronous File-Watch Baseline Loader**: Thread-safe watchdog observer (`PerplexityBaselineLoader`) initialized in the FastAPI lifespan context, enabling hot-reloads of `perplexity_baselines.yaml` without application restarts.
- **QualityDegradationAlertHandler in Alert Engine**: A Kafka-driven consumer handler that consumes the `alerts.quality.degradation` topic. Features rate limiting (deduplicated via Redis with a 1-hour TTL using the key format `rate_limit:quality_degradation:{model}:{endpoint}`).
- **Cold Start Suppressed Alerts**: Emitted degradation events feature an explicit `is_cold_start` boolean. If true (when baseline is `None`), the alert handler logs a warning but bypasses Slack notification to the `#llm-quality-alerts` channel.

---

## Failure-First System Building (FFSB) Analysis

### Mode 1: Perplexity Worker Outage or Latency Spikes
- **Symptom**: Timeout or worker crash blocks quality evaluation.
- **Prevention**: In `quality-engine` adapters, scorer HTTP queries are wrapped in a 500ms timeout budget. Any request exception defaults perplexity to `None`, dynamically reverting the composite scoring back to the 3-weight system safely.

### Mode 2: Baseline Missing on Cold Start
- **Symptom**: If the system initializes with empty Redis states, comparing incoming metrics to `None` could crash the alert pipeline or cause incorrect alert triggers.
- **Prevention**: Detection logic treats `baseline is None` as `is_cold_start = True`. Early returns suppress Slack messaging during these cold-start cycles.

### Mode 3: High-Perplexity Flag Explosion
- **Symptom**: Transient noise flags most calls as high-perplexity.
- **Prevention**: Dynamic p50 baselines are loaded from YAML config files, which can be dynamically adjusted or seeded using the `seed_baselines.py` script.

---

## Consequences

### Positive
- **Accurate Aggregation**: Adds perplexity as a key quality signal without breaking existing 3-weight setups when absent.
- **Hot-Reload Baselines**: Avoids restart overhead when fine-tuning baseline tolerances.
- **Alert Sanity**: Suppresses false positives during cold-starts via early check returns.

### Negative / Trade-offs
- **Complex Renormalization**: Variable weights footprint makes querying aggregate trends more difficult.
- **Watchdog Observer**: Running a watchdog folder observer thread introduces mild CPU tracking overhead in perplexity-worker instances.
