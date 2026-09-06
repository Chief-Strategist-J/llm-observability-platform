# Hypothesis — SLO Burn Rate Computation and Deduplication Reliability

## Research Objective
Evaluate the mathematical correctness of multi-window error-budget burn-rate computations and verify the robustness of Redis-based TTL alert deduplication locks.

## Hypotheses

1. **Hypothesis H-1 (Burn-Rate Convergence):** The multi-window calculation correctly reports a burn rate of $1.0$ when the error rate is exactly equal to the target budget (i.e. $1.0 - \text{compliance\_threshold}$), and maps accurately across 5m, 1h, and 6h windows.
2. **Hypothesis H-2 (Deduplication Lock Effectiveness):** Storing alert locks in Redis with unique `(severity, model, endpoint)` keys prevents alert redundancy, ensuring that subsequent workflow iterations within the TTL do not publish duplicate events.
3. **Hypothesis H-3 (Outage Resiliency):** In the event of a ClickHouse connection failure, the system falls back gracefully to a default threshold configuration ($0.95$) without raising uncaught exceptions or halting the scheduler.
