
> **How to use this template**
> One-line *"Why it's critical"* notes explain each section's purpose — strip them before external distribution.

---

# [System Name] — Solution / System Architecture Document

| Field | Value |
|---|---|
| Document ID | |
| Classification | Internal |
| Version | 1.0 |
| Status | Draft / In Review / Approved |
| Author(s) | |
| Approvers | |
| Date | |

---

## 1. Executive Summary
*Why it's critical: stakeholders outside engineering (product, finance, compliance) need to understand what's being built and why in one paragraph.*

- **Purpose:** what business problem this architecture solves.
- **Key architectural decisions (1-line each):**
- **Estimated cost/timeline impact:**

---

## 2. Business Context & Requirements

| Requirement | Type | Priority | Source |
|---|---|---|---|
| | Functional / Non-Functional | Must/Should/Could | Stakeholder/PRD ref |

**Non-Functional Requirements (NFRs) — quantified targets:**

| NFR | Target | Measurement Method |
|---|---|---|
| Availability | 99.9% | Uptime monitoring |
| Latency (p95) | < 200ms | APM |
| Throughput | X req/sec | Load test |
| RTO / RPO | | |
| Scalability | X users/records by [date] | |

---

## 3. Architecture Principles & Constraints
*Why it's critical: makes implicit trade-offs explicit so future decisions can be checked against a consistent rationale instead of re-litigated each time.*

| Principle | Rationale |
|---|---|
| e.g., "Prefer managed services over self-hosted" | Reduce ops burden, small team |

| Constraint | Type | Impact |
|---|---|---|
| e.g., Must run in EU region | Regulatory | Limits cloud provider region choice |

---

## 4. Logical Architecture
*Why it's critical: this is the primary diagram most readers will reference — it needs to stand alone without the prose.*

- **Diagram reference:** (`./evidence/logical-architecture.png`)

| Layer | Components | Responsibility |
|---|---|---|
| Presentation | | |
| Application/Service | | |
| Data | | |
| Integration | | |

---

## 5. Component Breakdown

| Component | Responsibility | Technology | Owner Team | Scaling Model |
|---|---|---|---|---|
| | | | | Horizontal/Vertical |

---

## 6. Data Architecture

| Data Store | Type | Data Classification | Retention Policy | Backup Strategy |
|---|---|---|---|---|
| | SQL/NoSQL/Object Store | | | |

- **Data flow diagram reference:** (`./evidence/data-flow.png`)
- **Data ownership/lineage notes:**

---

## 7. Integration Architecture

| Integration | Direction | Protocol | Sync/Async | Failure Handling |
|---|---|---|---|---|
| | Inbound/Outbound | REST/gRPC/Event | | Retry/DLQ/Circuit breaker |

---

## 8. Technology Stack

| Layer | Technology | Version | Justification |
|---|---|---|---|
| | | | |

---

## 9. Deployment Architecture

| Environment | Infrastructure | Deployment Method | Rollback Strategy |
|---|---|---|---|
| Prod | | CI/CD pipeline | Blue-green / Canary |

- **Diagram reference:** (`./evidence/deployment-diagram.png`)

---

## 10. Cross-Cutting Concerns
*Why it's critical: these are the concerns most often forgotten until an incident forces them in — better to design for them up front.*

| Concern | Approach |
|---|---|
| Security | link to Security Architecture Review |
| Observability | logging/metrics/tracing stack |
| Disaster Recovery | |
| Cost Management | |

---

## 11. Risks & Trade-offs

| Decision | Alternative Considered | Trade-off Accepted | Risk |
|---|---|---|---|
| | | | |

---

## 12. Appendix
- **A. Full diagrams**
- **B. Related ADRs**
- **C. Glossary**
- **D. Sign-off:** Architect, Eng Lead, Product Owner