> **How to use this template**
> One-line *"Why it's critical"* notes explain each section's purpose — strip them before external distribution. Structured around the industry-standard Well-Architected pillars (AWS/Azure/GCP all publish equivalents) so findings map cleanly to what cloud reviewers expect.

---

# [Environment/Workload Name] — Cloud & Infrastructure Architecture Review

| Field | Value |
|---|---|
| Report ID | |
| Classification | Confidential |
| Cloud Provider(s) | AWS / Azure / GCP / Multi-cloud |
| Review Date | |
| Reviewers | |
| Workload Owner | |

---

## 1. Executive Summary
*Why it's critical: leadership wants "is this costing us too much / is it going to fall over / is it compliant" — not a pillar-by-pillar deep dive.*

| Pillar | Rating | Top Issue |
|---|---|---|
| Security | Good/Fair/Poor | |
| Reliability | | |
| Performance Efficiency | | |
| Cost Optimization | | |
| Operational Excellence | | |
| Sustainability | | |

---

## 2. Scope

| Item | Detail |
|---|---|
| Workload(s) Reviewed | |
| Account(s)/Subscription(s) | |
| Regions | |
| Excluded Components | |

---

## 3. Current State Architecture
*Why it's critical: same principle as any architecture doc — the diagram is the shared reference everything else in the report points back to.*

- **Diagram reference:** (`./evidence/cloud-architecture.png`)

| Resource Type | Count | Purpose |
|---|---|---|
| Compute (VM/Container/Serverless) | | |
| Storage | | |
| Database | | |
| Networking (VPC/Subnets/LB) | | |

---

## 4. Pillar Review: Security
*Why it's critical: cloud misconfigurations (open S3 buckets, over-permissioned IAM) are consistently the top real-world breach cause — this pillar gets first attention for a reason.*

| Check | Status | Finding |
|---|---|---|
| IAM least privilege | Pass/Fail | |
| Public exposure audit (storage, DBs) | | |
| Encryption at rest/in transit | | |
| Secrets management (no hardcoded keys) | | |
| Network segmentation (VPC/SG rules) | | |
| Logging (CloudTrail/Activity Log enabled) | | |

---

## 5. Pillar Review: Reliability

| Check | Status | Finding |
|---|---|---|
| Multi-AZ / redundancy | | |
| Backup & restore tested | | |
| Auto-scaling configured | | |
| Disaster recovery plan (RTO/RPO defined) | | |
| Single points of failure identified | | |

---

## 6. Pillar Review: Performance Efficiency

| Check | Status | Finding |
|---|---|---|
| Right-sized compute instances | | |
| Caching strategy | | |
| Database indexing/query performance | | |
| CDN usage for static content | | |

---

## 7. Pillar Review: Cost Optimization
*Why it's critical: unreviewed cloud spend grows silently — this is usually the section that pays for the review itself.*

| Check | Status | Finding | Est. Monthly Savings |
|---|---|---|---|
| Unused/idle resources | | | |
| Reserved/committed use discounts applicable | | | |
| Storage tiering (hot/cold) | | | |
| Right-sizing opportunities | | | |

---

## 8. Pillar Review: Operational Excellence

| Check | Status | Finding |
|---|---|---|
| Infrastructure as Code coverage | | |
| CI/CD pipeline maturity | | |
| Monitoring & alerting coverage | | |
| Runbooks/documentation current | | |

---

## 9. Pillar Review: Sustainability

| Check | Status | Finding |
|---|---|---|
| Region selection (carbon-aware) | | |
| Resource utilization efficiency | | |

---

## 10. Findings & Recommendations

| Finding ID | Pillar | Recommendation | Priority | Effort | Owner | Target Date |
|---|---|---|---|---|---|---|
| C-01 | | | P0/P1/P2 | S/M/L | | |

---

## 11. Roadmap

| Phase | Actions | Timeline |
|---|---|---|
| Immediate (0–30 days) | | |
| Short-term (1–3 mo) | | |
| Long-term (3–12 mo) | | |

---

## 12. Appendix
- **A. Full resource inventory export**
- **B. Cost breakdown detail**
- **C. IAM policy audit detail**
- **D. Sign-off:** Cloud Architect, Security, FinOps