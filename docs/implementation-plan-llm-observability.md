# LLM Observability Platform — Implementation Plan

## Scope and Goals
This plan translates the requested architecture into an implementation-ready roadmap for:
- Instrumentation layer
- Cost tracking layer
- Quality monitoring layer
- Latency analysis layer
- Prompt intelligence layer
- Language-specific isolated package structure

## Guiding Constraints
- Every language sub-package is fully isolated.
- No runtime cross-sub-package source imports.
- Runtime communication always uses versioned contracts + generated clients.
- `{lang}-shared` packages contain types + pure utils only (no IO, no business logic).

---

## Phase 0 — Repository Foundation and Package Topology

### Deliverables
1. Create language roots and isolation boundaries:
   - `packages/python/*`
   - `packages/rust/*`
   - `packages/go/*`
   - `packages/node/*`
   - `packages/java/*`
   - `packages/apis/` (stage 2+)
2. Introduce per-language shared packages:
   - `python-shared`, `rust-shared`, `go-shared`, `node-shared`, `java-shared`
3. Add import guard rules in every language to block cross-package runtime imports.
4. Add CI checks that fail on forbidden imports.

### Acceptance Criteria
- Cross-package runtime imports fail CI.
- Each sub-package builds/tests independently.
- Shared packages expose only index-based exports for types/utils.

---

## Phase 1 — Instrumentation Layer (Foundational Spans)

### 1.1 Automatic span capture for every LLM call
Capture these attributes on every call:
- `model`
- `prompt_tokens` (exact via `tiktoken` or equivalent exact tokenizer)
- `completion_tokens`
- `latency_ms_ttft`
- `latency_ms_total`
- `finish_reason`
- `cost_usd`

### 1.2 Sampled enrichment (1% traffic)
For sampled calls capture:
- `prompt_hash` = SHA256(prompt)
- `prompt_embedding` (MiniLM 384)
- `response_embedding` (MiniLM 384)
- `quality_score` (composite)

### 1.3 Tracing implementation
- Add OpenTelemetry tracer + middleware in each runtime package under `src/infra/tracing/`.
- Standardize span naming and tags:
  - Span name: `llm.call`
  - Required tags: `service`, `endpoint`, `user_id`, `session_id`, `model`, `provider`

### Acceptance Criteria
- 100% LLM calls produce a structured span.
- Token counts are exact (not estimated).
- Sampled enrichment rate remains near 1% ± tolerance.

---

## Phase 2 — Cost Tracking Layer

### 2.1 Per-call pricing engine (O(1))
Compute:
- `cost = input_tokens * price_input + output_tokens * price_output`

Maintain provider/model pricing table with effective dates.

### 2.2 Real-time aggregation via Fenwick Trees
Maintain Fenwick trees per dimension:
- `model`, `service`, `user_id`, `session_id`, `endpoint`

Time windows:
- 1 minute, 1 hour, 1 day, 1 month

Query complexity target:
- Any time range in `O(log n)`

### 2.3 Budget enforcement (token bucket)
Per `(user_id, model)`:
- Refill at configured rate
- Validate before each LLM call
- Block when exhausted
- Alert at 80% consumption

### 2.4 Cost anomaly detection
- EWMA baseline per `(service, model, hour-of-week)`
- Alert when `current_cost > 3x EWMA`
- Attach top prompt-cluster contributors for investigation

### Acceptance Criteria
- Per-call cost produced in real-time.
- Budget checks applied pre-call path.
- Alerts emitted for threshold and anomaly breaches.

---

## Phase 3 — Quality Monitoring Layer (Sampled 1%)

### 3.1 Score components
1. **Semantic coherence**
   - Cosine similarity(prompt embedding, response embedding)
   - Alert if `< 0.3`
2. **Faithfulness (RAG)**
   - DeBERTa NLI sentence-level entailment
   - `faithfulness = entailed_sentences / total_sentences`
   - Alert if `< 0.7`
3. **Toxicity**
   - Perspective API or local classifier score [0,1]
   - Alert if `> 0.5`
4. **Perplexity proxy**
   - Perplexity of response text
   - Compare to baseline by prompt type

### 3.2 Aggregate score
- Weighted score from all components.
- Dashboard trends per model and endpoint.
- Alert if aggregate quality drops `>10%` vs 7-day baseline.

### Acceptance Criteria
- Quality pipeline runs on sampled traffic.
- Low-quality and hallucination risk alerts are actionable.

---

## Phase 4 — Latency Analysis Layer

### 4.1 Metrics captured
- TTFT (time to first token)
- TPOT (time per output token)
- Total latency

### 4.2 Statistical tracking
- DDSketch per model for P50/P95/P99.
- Baselines per model and time-of-day.
- Alert if TTFT P99 `>2x` baseline.

### 4.3 Attribution breakdown
Track segmented latency:
- Network (DNS/TCP/TLS)
- Queue wait
- Model processing

### 4.4 SLO + burn rate
- Interactive SLO: `P95 total latency < 3s`
- Implement burn-rate alerts (same algorithm as System 4 spec).

### Acceptance Criteria
- Dashboard shows TTFT/TPOT/total latency with percentile bands.
- Attribution identifies dominant bottleneck component.

---

## Phase 5 — Prompt Intelligence Layer

### 5.1 Clustering
- Embed sampled prompts with MiniLM.
- HDBSCAN to discover clusters.
- Cluster naming through LLM summaries of representative prompts.
- Track cost/quality/latency per cluster.

### 5.2 Duplicate detection
- MinHash signatures (`k=128`)
- LSH bands (`b=16`, `r=8`) for candidates
- Exact Jaccard verification
- Compute dedup rate and caching opportunity

### 5.3 Drift detection
- Cluster centroid over time
- ADWIN for drift events
- Alert with contextual explanations (likely product/user behavior changes)

### 5.4 Token efficiency
- Token count vs information density metrics
- Flag verbose/low-density prompts
- Estimate savings via LLMLingua-style compression

### Acceptance Criteria
- Prompt clusters available in analytics UI.
- Drift and dedup signals tied to cost impact.

---

## Contracts-First Delivery Model (Per Sub-Package)

For each package, implement in this order:
1. `contracts/` authored first (`openapi/graphql/proto/asyncapi` as needed)
2. Generate clients into `src/infra/clients/{upstream-service}/v1/`
3. Implement handlers/services/repositories behind the contract
4. Add contract tests (REST/GraphQL/gRPC/events)

No runtime integration is allowed before a versioned contract exists.

---

## Package Skeleton Standard (Universal)
Each package will adopt the provided universal structure, including:
- `contracts/`
- `src/{api,features,infra,shared}`
- `database/{migrations,seeds,schema.lock}`
- `tests/{unit,integration,contract,e2e,performance}`
- `scripts/`, `deploy/`, `build/`, CI workflows

---

## Initial Execution Backlog (Start Applying)

### Sprint A (Week 1)
- Scaffold package topology and shared packages.
- Add import guards + CI enforcement.
- Introduce base OpenTelemetry middleware and `llm.call` span schema.

### Sprint B (Week 2)
- Implement exact token counting + per-call pricing engine.
- Add Fenwick aggregation service and query API.
- Add token bucket checks in pre-call middleware.

### Sprint C (Week 3)
- Implement sampled embedding pipeline and quality component scoring.
- Stand up DDSketch latency percentiles and baseline comparison.

### Sprint D (Week 4)
- Implement MinHash LSH dedup + HDBSCAN clustering + ADWIN drift.
- Add dashboards and alert wiring for cost/quality/latency/prompt intelligence.

---

## Definition of Done
- All layers implemented with automated tests and SLO/alert coverage.
- CI gates enforce isolation, linting, typing, security, and coverage requirements by language.
- Runtime cross-package communication uses only generated clients from versioned contracts.
- Operational dashboards provide real-time visibility into cost, quality, latency, and prompt patterns.
