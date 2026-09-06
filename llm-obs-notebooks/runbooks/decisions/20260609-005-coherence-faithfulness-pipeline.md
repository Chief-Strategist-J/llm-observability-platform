# ADR-005 — Phase 2 Coherence + Faithfulness Pipeline Implementation

| Field       | Value                                                             |
|-------------|-------------------------------------------------------------------|
| **ID**      | 005                                                               |
| **Date**    | 2026-06-09                                                        |
| **Status**  | accepted                                                          |
| **Deciders**| LLM Observability Platform Team                                   |
| **Package** | `packages/python/quality-engine`                                  |

---

## Context

As part of the LLM Observability Platform's Layer 3 quality aggregation service, we required a robust mechanism to compute and aggregate semantic coherence and faithfulness scores for sampled LLM spans. Specifically, we needed to:
1. Optimize embedding generation by reusing existing embeddings (`prompt_embedding` and `response_embedding`) present on the incoming span instead of unconditionally requesting them from the downstream embedding-worker.
2. Track embedding reuse hit/miss rates via Prometheus metrics for observability.
3. Classify and flag semantic coherence (low coherence vs OK) using prompt-type thresholds (Chat: 0.30, RAG: 0.25, Code: 0.15, Classification: 0.40) and flag hallucination risks (score < 0.70) on faithfulness results.
4. Scale timeouts for HTTP queries to downstream scorers under tight limits (e.g. 2000ms for faithfulness POST `/nli` queries).
5. Exclude perplexity scores from composite score calculations for now (weight = 0.0), and dynamically renormalize the remaining active sub-scorer weights when one or more scores are absent.
6. Persist composite scores, sub-scorer results, and the active `weights_used` structure back to the database.

---

## Decision

We implemented the following architectural and design decisions:
- **Individual Embedding Reuse**: Modified [handler.py](file:///home/btpl-lap-22/live/obs/packages/python/quality-engine/src/handlers/span_quality/handler.py) to evaluate and fetch prompt and response embeddings independently. This maximizes reuse rates since a span may have one pre-computed embedding but not the other.
- **Prometheus Metrics Instrumentation**: Added `EMBEDDING_REUSE` (`quality_embedding_reuse_total` counter with `status` labels: `"reused"` vs `"generated"`) to track the efficiency of embedding caching and reuse.
- **Dynamic Weight Renormalization & Perplexity Exclusion**: Adjusted weights in [composite_scorer.py](file:///home/btpl-lap-22/live/obs/packages/python/quality-engine/src/handlers/span_quality/composite_scorer.py) and [rules.py](file:///home/btpl-lap-22/live/obs/packages/python/quality-engine/src/features/score_composite/rules.py) to use:
  - Coherence: 0.30
  - Faithfulness: 0.40
  - Toxicity: 0.20
  - Perplexity: 0.0 (excluded)
  If any of these metrics are absent, the active weights are normalized to sum to `1.0`.
- **Database Schema Migration Isolation**: Schema modifications such as persisting `weights_used` must follow database immobility rules. We must isolate new columns and table constraints into separate numbered migration files rather than modifying the baseline migrations.
- **Scorer Thresholds & Flag Propagation**: Propagated threshold flags (`LOW_COHERENCE` and `HALLUCINATION_RISK`) directly into the `quality_flags` database list representation.

---

## Failure-First System Building (FFSB) Analysis

Applying the failure-first framework:

### Mode 1: Downstream Embedding / Scorer Timeout or Outage
- **Symptom**: Outages of the embedding-worker or the nli-worker stall the Temporal workflow pipeline, causing ingestion delays.
- **Prevention**:
  - Implement a tight HTTP timeout client budget (500ms for embedding calls, 2000ms for NLI/faithfulness calls).
  - Wrap downstream calls in try-catch loops, log warning metrics, and return `None` rather than raising hard exceptions. The composite scorer dynamically renormalizes the remaining active weights so the span is successfully processed and saved.

### Mode 2: Invariant Validation Failures
- **Symptom**: Out-of-bounds scores or missing required metrics violate system invariants (INV-Q-01 through INV-Q-07) and crash the database ingestion process.
- **Prevention**:
  - Validate invariants explicitly inside [composite_scorer.py](file:///home/btpl-lap-22/live/obs/packages/python/quality-engine/src/handlers/span_quality/composite_scorer.py).
  - Violations emit Prometheus warning logs but never block execution or prevent database writing, maintaining ingest reliability.

### Mode 3: Dynamic Weight Renormalization Division by Zero
- **Symptom**: If all sub-scorer metrics are absent (e.g. timeout on all endpoints), the sum of active weights becomes `0.0`, triggering a division-by-zero error.
- **Prevention**:
  - Implement safe guarding checks inside [rules.py](file:///home/btpl-lap-22/live/obs/packages/python/quality-engine/src/features/score_composite/rules.py): if `total_weight <= 0.0`, return a `None` composite score and empty `weights_used` dictionary.

---

## Consequences

### Positive
- **Improved Performance**: Reusing embeddings avoids unnecessary HTTP roundtrips.
- **Higher Observability**: The `weights_used` JSONB column logs the exact contributions of sub-scorers at write-time, enabling clear debugging of composite scores for non-RAG vs RAG spans.
- **Resilience**: Invariant violations do not block span ingestion, and network timeouts fall back safely to partial score renormalization.

### Negative / Trade-offs
- **Renormalization Complexity**: The scoring footprint varies per span, requiring query consumers to fetch `weights_used` to understand how the score was aggregated.
