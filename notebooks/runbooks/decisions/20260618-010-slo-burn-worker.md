# ADR-010 — SLO Burn Rate Evaluation and Multi-Window Alerting Worker

| Field       | Value                                                             |
|-------------|-------------------------------------------------------------------|
| **ID**      | 010                                                               |
| **Date**    | 2026-06-18                                                        |
| **Status**  | accepted                                                          |
| **Deciders**| LLM Observability Platform Team                                   |
| **Package** | `packages/python/slo-burn-worker`                                 |

---

## Context

To protect the platform's user experience and maintain reliable operation of various LLM deployments, we needed an alerting engine that:
1. **Minimizes Alert Fatigue:** Standard threshold alerting suffers from high noise (transient spikes trigger paging) or slow detection (small, sustained budget burn takes hours to detect).
2. **Implements Multi-Window Multi-Burn-Rate Alerts:** Use Google SRE best practices to monitor error budgets across three rolling windows (5m, 1h, 6h) and route alerts based on the severity of budget depletion.
3. **Ensures Precise Interval Orchestration:** Run computations every 60 seconds without clock drift or race conditions.
4. **Handles Deduplication:** Prevent multiple notifications for the same issue using TTL-based lock states.
5. **Mitigates Database Dependencies:** Prevent worker crashes when Redis, Kafka, or ClickHouse are unreachable.

---

## Decision

We built and registered `slo-burn-worker` using the following architectural design:

- **Temporal Schedule Orchestration:** Configured a native Temporal schedule (`slo-burn-rate-schedule`) running every 60 seconds to execute `SloBurnWorkflow`. This guarantees drift-free execution compared to standard OS cron.
- **Three-Window Burn-Rate Computation:** Analyzes the error rate (defined as requests exceeding baseline latencies or returning system errors) over three windows:
  * **Fast Window (5 min):** Immediate indicator of catastrophic outages.
  * **Medium Window (1 hour):** Captures high-rate degradations.
  * **Slow Window (6 hours):** Identifies slow-burning budget erosion.
- **State-driven Alert Severity Routing:**
  * **Page:** Activated if Fast Burn Rate $> 14.4$ AND Medium Burn Rate $> 6.0$.
  * **Slack:** Activated if Medium Burn Rate $> 6.0$ AND Slow Burn Rate $> 3.0$ (and Page condition is not met).
  * **Ticket:** Activated if Slow Burn Rate $> 1.0$ (and Page or Slack are not met).
- **Redis-Backed Alert Deduplication Locks:** Alert actions acquire a lock key (`alert_lock:{severity}:{model}:{endpoint}`) in Redis with specific TTLs (e.g., 1 hour for page/slack, 24 hours for ticket) to suppress repetitive notifications.
- **Fail-Safe Fallbacks:**
  * **ClickHouse Outages:** Falls back to a configurable default compliance threshold ($0.95$) if ClickHouse is unreachable during baseline p95 extraction.
  * **Redis Outages:** Retries connection automatically; workflow execution blocks securely until Redis is restored, preserving state.

---

## Failure-First System Building (FFSB) Analysis

### Mode 1: ClickHouse Latency Checkpoint Queries Fail
- **Symptom**: Worker cannot query historical baseline latencies.
- **Prevention**: Implemented a fallback mechanism in `SloBurnActivities.compute_burn_rates`. If the baseline query fails, it reads default configurations from `slo_compliance_config.yaml` or falls back to `0.95` compliance threshold.

### Mode 2: Redis Outage during Deduplication Checks
- **Symptom**: Lock checking fails, leading to potential alert storms.
- **Prevention**: Utilizes Temporal's native activity retry policies. If Redis throws a connection error, the deduplication activity is retried with exponential backoff up to a maximum duration of 1 hour, pausing workflow progress safely.

### Mode 3: Kafka Broker Failure
- **Symptom**: Alerts cannot be emitted onto the `alerts.latency.slo` topic.
- **Prevention**: Activity `handle_alerts` wraps Kafka publication in retry blocks. Unsent alerts are kept in the activity execution context, and the activity fails and retries via Temporal task queue configuration rather than discarding the events.

---

## Consequences

### Positive
- **Drift-Free Scheduling:** Temporal schedules provide reliable cron execution and detailed execution history.
- **Zero Alert Storms:** Deduplication locks prevent engineers from being paged repeatedly during an ongoing incident.
- **Resilient Baselines:** Standard fallback YAML ensures continuous SLO evaluation even during ClickHouse maintenance windows.

### Negative / Trade-offs
- **Temporal Dependency:** Critical dependency on the Temporal server being healthy for orchestration.
- **State Persistence Risk:** Keeping untransmitted alert states inside Temporal workflows increases execution state size during extended Kafka broker outages.
