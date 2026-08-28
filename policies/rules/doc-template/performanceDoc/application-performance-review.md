> **How to use this template**
> One-line *"Why it's critical"* notes explain each section's purpose — strip them before external distribution.
> Difference from the Load Test report: this is a review of **real production behavior over time** (using APM data), not a controlled synthetic test.

---

# [Application Name] — Application Performance Review

| Field | Value |
|---|---|
| Report ID | |
| Review Period | |
| APM Tool(s) Used | Datadog / New Relic / Dynatrace / Grafana |
| Author(s) | |

---

## 1. Executive Summary
*Why it's critical: this typically feeds a "why does the app feel slow" question from leadership or a customer escalation — lead with the answer.*

| Metric | Current | Baseline/SLA | Status |
|---|---|---|---|
| Avg response time | | | |
| p95 response time | | | |
| Error rate | | | |
| Apdex score | | | |
| Availability | | | |

---

## 2. Scope & Methodology

| Item | Detail |
|---|---|
| Services/Endpoints Reviewed | |
| Time Window Analyzed | |
| Data Source | APM traces, RUM, logs |
| Comparison Baseline | Previous quarter / SLA target |

---

## 3. Key Metrics Over Time
*Why it's critical: a single-point-in-time number hides whether performance is degrading gradually — trend lines catch slow leaks before they become outages.*

| Metric | Week 1 | Week 2 | Week 3 | Week 4 | Trend |
|---|---|---|---|---|---|
| p95 latency | | | | | ↑/↓/→ |
| Error rate | | | | | |
| Throughput | | | | | |

---

## 4. Hotspot Analysis
*Why it's critical: this is where effort should actually go — the slowest 5% of endpoints usually account for the majority of user-perceived slowness.*

| Endpoint/Query | Avg Time | Call Volume | % of Total Time | Trend |
|---|---|---|---|---|
| | | | | |

**Slowest database queries:**

| Query | Avg Duration | Calls/min | Index Used? |
|---|---|---|---|
| | | | |

---

## 5. Root Cause Analysis

| Issue | Root Cause | Affected Endpoints |
|---|---|---|
| | N+1 query / missing index / unbounded payload / sync call in hot path / GC pauses | |

---

## 6. Error Analysis

| Error Type | Count | Endpoints Affected | Trend |
|---|---|---|---|
| 5xx | | | |
| Timeouts | | | |
| Client-side JS errors (if RUM used) | | | |

---

## 7. Infrastructure Correlation

| Metric | Correlates With Latency Spike? | Notes |
|---|---|---|
| CPU utilization | Yes/No | |
| Memory/GC activity | | |
| DB connection pool saturation | | |
| Downstream service latency | | |

---

## 8. Optimization Recommendations

| ID | Recommendation | Expected Gain | Effort | Priority | Owner |
|---|---|---|---|---|---|
| O-01 | Add index on `table.column` | -150ms p95 on endpoint X | S | P0 | |

---

## 9. Validation Plan
*Why it's critical: closes the loop — without a re-measurement, "optimizations" are assumed to work rather than confirmed.*

| Recommendation ID | Validation Method | Target Metric | Status |
|---|---|---|---|
| O-01 | Re-run APM comparison post-deploy | p95 < Xms | Pending |

---

## 10. Appendix
- **A. Full APM dashboards (links)**
- **B. Query execution plans**
- **C. Flame graphs / trace waterfalls referenced**