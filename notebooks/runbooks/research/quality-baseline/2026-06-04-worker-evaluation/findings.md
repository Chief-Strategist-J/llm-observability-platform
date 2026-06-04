# Findings: Quality Baseline Worker Implementation \& Rollup Evaluation

This document details the performance characterization and database lock contention analysis of the quality baseline and trend rollup worker. For the rigorous mathematical formulations, variance bounds, and alerting sensitivity proofs, please refer to the compiled [proof.pdf](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/research/quality-baseline/2026-06-04-worker-evaluation/proof.pdf).

## Key Outcomes

- **Resource Savings on Hot-Paths**: Offloading the PostgreSQL rolling average calculation to an asynchronous Temporal workflow saves massive database resources. The database load scales down significantly, preventing database connection pool exhaustion and CPU starvation.
- **Improved Hot-Path Latency**: Upstream scoring services read from the Redis cache in sub-millisecond time instead of executing synchronous table scan aggregates.
- **Guaranteed Alert Sensitivity**: The alerting triggers are designed to detect prompt quality score degradations swiftly, triggering Slack notifications within 24 hours of a drift event.
- **Visualized Trend Verification**: A simulated 30-day run verified that the rolling baseline tracks scores accurately and triggers the alert system immediately upon degradation.

---

## 1. Estimator Stability \& Variance Analysis

The quality baseline worker computes rolling averages over a trailing window of historical scores. Running this out-of-band ensures that the calculated baseline cached in Redis remains stable and converges to the true performance mean of the models without impacting front-end users. The detailed proofs for variance boundedness and estimator convergence are documented in [proof.pdf](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/research/quality-baseline/2026-06-04-worker-evaluation/proof.pdf).

---

## 2. Alerting Sensitivity & Detection Latency

The alerting mechanism is calibrated to trigger a quality degradation alert if the daily average quality score falls below a configured fraction of the rolling baseline. The mathematical model proves that the system will automatically detect and report any major prompt quality degradation within exactly one day of the drift event. The formal step-change derivation and detection threshold constraints are detailed in [proof.pdf](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/research/quality-baseline/2026-06-04-worker-evaluation/proof.pdf).

---

## 3. Computational Complexity \& Database Lock Contention

We compare the system behavior under synchronous (in-band) vs asynchronous (out-of-band) aggregation:

| Performance Metric | Synchronous In-band | Asynchronous Out-of-band (Worker) |
|---|---|---|
| **Hot Path Latency** | High (table scan latency) | Sub-millisecond (Redis cache lookup) |
| **Query Complexity** | Scales quadratically with request rate and window size | Scales linearly with request rate, executing only once per hour |
| **Database Pool Locks** | High (frequent long-running aggregates cause starvation) | Negligible (query runs in background on a separate worker) |
| **System Stability** | Vulnerable to database connection cascade failures | Bounded, resilient under high request volumes |

---

## 4. Visual Verification Outcomes

The simulation results are stored in the following files:
*   **Dataset:** [simulated_scores.csv](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/research/quality-baseline/2026-06-04-worker-evaluation/data/simulated_scores.csv)
*   **Plot:** [drift_alert.png](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/research/quality-baseline/2026-06-04-worker-evaluation/outputs/drift_alert.png)

Below is the visualized baseline drift and alerting output from the research notebook:

![Quality Baseline Drift and Alert Ingestion Plot](/home/btpl-lap-22/live/obs/notebooks/runbooks/research/quality-baseline/2026-06-04-worker-evaluation/outputs/drift_alert.png)

---

## Links
*   [research.ipynb](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/research/quality-baseline/2026-06-04-worker-evaluation/research.ipynb)
*   [hypothesis.md](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/research/quality-baseline/2026-06-04-worker-evaluation/hypothesis.md)
*   [proof.tex](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/research/quality-baseline/2026-06-04-worker-evaluation/proof.tex)
*   [ADR-003: Quality Baseline and Trend Rollup Worker](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/decisions/20260604-003-quality-baseline-worker.md)
