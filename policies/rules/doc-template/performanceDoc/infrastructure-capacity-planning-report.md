> **How to use this template**
> One-line *"Why it's critical"* notes explain each section's purpose — strip them before external distribution.
> Difference from the other performance docs: this is **forward-looking** (will we run out of capacity, and when) rather than diagnosing current behavior.

---

# [Environment Name] — Infrastructure Capacity Planning Report

| Field | Value |
|---|---|
| Report ID | |
| Planning Horizon | e.g., next 12 months |
| Author(s) | |
| Date | |

---

## 1. Executive Summary
*Why it's critical: budget and procurement decisions get made off this section alone — it needs a clear "we run out of X in Y months" statement.*

| Resource | Current Utilization | Projected Exhaustion Date | Action Needed By |
|---|---|---|---|
| Compute | | | |
| Storage | | | |
| Database | | | |
| Network Bandwidth | | | |

---

## 2. Current Utilization Overview

| Resource | Total Capacity | Current Usage | Utilization % | Peak Usage (last 90 days) |
|---|---|---|---|---|
| CPU (aggregate) | | | | |
| Memory | | | | |
| Storage | | | | |
| Database connections | | | | |
| Network throughput | | | | |

---

## 3. Growth Drivers
*Why it's critical: capacity forecasts based purely on historical growth miss known step-changes (a new product launch, a big customer onboarding) — this section captures what history can't.*

| Driver | Expected Impact | Timeline | Confidence |
|---|---|---|---|
| e.g., New enterprise customer onboarding | +30% data volume | Q3 | High |
| e.g., Feature launch X | +20% API traffic | Q4 | Medium |

---

## 4. Capacity Forecast

| Resource | Q1 | Q2 | Q3 | Q4 | Capacity Ceiling |
|---|---|---|---|---|---|
| Compute (cores) | | | | | |
| Storage (TB) | | | | | |
| Database (IOPS) | | | | | |

**Forecast methodology:** linear trend / seasonal model / driver-adjusted — state which and why.

---

## 5. Risk of Exhaustion

| Resource | Time to Exhaustion (at current trend) | Impact if Exhausted | Severity |
|---|---|---|---|
| | | Service degradation / outage / hard failure | Critical/High/Med |

---

## 6. Scaling Options

| Resource | Option | Type | Cost Impact | Lead Time |
|---|---|---|---|---|
| Compute | Vertical scale-up | Quick fix | | Immediate |
| Compute | Horizontal auto-scaling | Structural | | Days–weeks |
| Database | Read replicas / sharding | Structural | | Weeks |
| Storage | Tiering / archival policy | Cost optimization | | Days |

---

## 7. Cost Implications
*Why it's critical: capacity planning without cost context leads to over-provisioning "just to be safe" — this keeps the recommendation grounded in budget reality.*

| Scaling Option | Estimated Monthly Cost Change | Break-even vs. Downtime Risk |
|---|---|---|
| | | |

---

## 8. Recommendations & Timeline

| ID | Recommendation | Resource | Priority | Target Date | Owner |
|---|---|---|---|---|---|
| C-01 | | | P0/P1/P2 | | |

---

## 9. Appendix
- **A. Raw utilization data / dashboard links**
- **B. Forecast model details/assumptions**
- **C. Vendor quotes (if applicable)**