# ADR 0002: Kafka Publisher for Flagged Toxicity Events

| Field | Value |
| --- | --- |
| **ADR ID** | `ADR-PYTHON-TOXICITY-0002` |
| **Title** | Publish Flagged Toxicity Events to Kafka Topic `llm.toxicity.flagged` |
| **Status** | **Accepted** |
| **Date** | 2026-06-02 |
| **Scope** | `packages/python/toxicity` — event publishing, Kafka integration, flagging threshold |

---

## 1. Context & Problem Statement

When the toxicity scorer determines a response is toxic (`primary_score > 0.50`), how should downstream systems (alerting, dashboards, human-review queues) learn about it — given:

- The scorer runs synchronously in the span-enrichment pipeline.
- Downstream consumers are decoupled services with independent lifecycles.
- The caller (span enrichment service) must not be blocked waiting for downstream consumers.
- Kafka (`llm.spans.raw`, `llm.spans.sampled`) is already the platform's standard async event bus.

---

## 2. Failure Modes We Are Solving

| ID | Symptom | Root Cause | Severity |
|---|---|---|---|
| **FM-01** | Downstream alerting service misses toxic events | No pub/sub mechanism between scorer and consumer | CRITICAL — safety gap |
| **FM-02** | Span enrichment pipeline blocked by slow consumer | Synchronous HTTP callback to downstream | HIGH — latency cascades to trace ingestion |
| **FM-03** | Flagged events lost on scorer restart | In-memory queue with no persistence | HIGH — safety audit gap |

---

## 3. Decision Drivers

- **D1**: Flagged events must not block the scoring HTTP response path.
- **D2**: Must use the existing Kafka cluster — no new infrastructure.
- **D3**: Publisher must be **optional** — scorer must function correctly when `KAFKA_BOOTSTRAP_SERVERS` is unset (test environments, local dev).
- **D4**: Each flagged event must carry `trace_id`, `span_id`, `score`, and per-label `scores` for downstream correlation.
- **D5**: Publishing failure must not cause a `500` to the API caller — scoring result must still be returned.

---

## 4. Options Considered

### Option A — Synchronous HTTP webhook to downstream services *(rejected)*
- Solves: FM-01.
- Does not solve: FM-02 (blocks caller), FM-03 (no durability).
- **Eliminated**: violates D1 — blocks scoring response path.

### Option B — Kafka `llm.toxicity.flagged` topic via `confluent-kafka` *(chosen)*
- Solves: FM-01, FM-02 (fire-and-forget `produce` + `flush`), FM-03 (Kafka retention).
- Creates: publisher as soft dependency — must not fail hard if broker unreachable (D3).

### Option C — Redis Streams *(rejected)*
- Solves: FM-01, FM-02.
- Does not solve: FM-03 (Redis eviction policy, no guaranteed retention).
- **Eliminated**: Kafka is the platform standard; Redis is for ephemeral state.

### Option D — Write to AlloyDB directly *(rejected)*
- Solves: FM-01, FM-03.
- Does not solve: FM-02 (DB write adds ~5–20ms per request, blocks on connection pool).
- **Eliminated**: synchronous DB write in scoring hot path is unacceptable.

---

## 5. Decision Outcome

**Chosen: Option B — `confluent-kafka` producer publishing to `llm.toxicity.flagged`.**

### Key design decisions:

1. **Optional publisher**: `KafkaToxicityPublisherAdapter(bootstrap_servers=None)` is a no-op. The app factory reads `KAFKA_BOOTSTRAP_SERVERS` from env; if unset, publishing is silently disabled. Scorer still runs and returns results.

2. **Lazy producer init**: `confluent-kafka` `Producer` is created on first `publish_flagged()` call via `@property` — avoids broker connection at startup.

3. **Fire-and-forget with `flush()`**: `produce()` enqueues the message, `flush()` waits for the internal librdkafka queue to drain synchronously before returning. This is acceptable because `flush()` returns in ~1ms when the broker is reachable.

4. **Payload schema**:
```json
{
  "trace_id": "string",
  "span_id": "string",
  "score": 0.87,
  "scores": {
    "toxicity": 0.87,
    "severe_toxicity": 0.12,
    "obscene": 0.43,
    "threat": 0.05,
    "insult": 0.31,
    "identity_hate": 0.08
  },
  "flag": "TOXIC_RESPONSE"
}
```

5. **Threshold**: `score > 0.50` (strict greater-than). Score of exactly `0.50` is not flagged. Constant `TOXICITY_THRESHOLD = 0.50` in `core/domain/rules.py`.

---

## 6. Failure Modes Created

| ID | Name | Symptom | Detection | Threshold | Recovery | Prevention |
|---|---|---|---|---|---|---|
| **FM-NEW-01** | Broker unreachable at publish time | `flush()` blocks until `delivery.timeout.ms` | Monitor `confluent_kafka` delivery error callback | Timeout > 2s | Return scoring result anyway — do not propagate exception | Wrap `publish_flagged` in try/except; log error, do not re-raise |
| **FM-NEW-02** | `llm.toxicity.flagged` topic not provisioned | `KafkaException: UNKNOWN_TOPIC_OR_PART` | App startup smoke test / migration check | Any exception at first `produce` | Create topic via migration script | Include topic in `contracts/registries/topics.yaml` migration |
| **FM-NEW-03** | Publisher silently disabled in prod | Flagged events never appear in Kafka | Monitor `llm_toxicity_publish_total` counter; alert if zero over 1h with non-zero scoring volume | 0 publishes over 1h | Check `KAFKA_BOOTSTRAP_SERVERS` env var; restart service | Startup log: emit `WARNING` if `KAFKA_BOOTSTRAP_SERVERS` unset |

---

## 7. Consequences

### Positive
- Downstream consumers (alerting, human-review, dashboard) are fully decoupled from the scorer.
- Scorer API latency unaffected by downstream consumer health.
- `trace_id` + `span_id` in payload enables cross-service trace correlation in Tempo.
- No-op publisher makes local dev / unit tests work without Kafka.

### Negative
- At-least-once delivery — consumers must be idempotent on `(trace_id, span_id)`.
- If `flush()` blocks (broker slow), the `/score` HTTP response is delayed by up to `delivery.timeout.ms` (default 300s — **must be reduced to 2s** via producer config).
- Topic `llm.toxicity.flagged` must be provisioned before first deployment — add to migration spec.

---

## 8. Review Trigger

Revisit if:
- Publishing lag causes `/score` p99 to exceed 500ms.
- Flagged event volume exceeds 10,000/min (consider async producer with background thread).
- A downstream consumer requires exactly-once semantics (switch to transactional producer).
