> **How to use this template**
> One-line *"Why it's critical"* notes explain each section's purpose — strip them before sharing broadly. This sits one level below the Solution Architecture Doc — it's the implementation-level design for a single feature/service, written before coding starts.

---

# [Feature/Service Name] — Technical Design Document

| Field | Value |
|---|---|
| Document ID | |
| Status | Draft / In Review / Approved / Implemented |
| Author(s) | |
| Reviewers | |
| Related Architecture Doc / ADRs | |
| Date | |

---

## 1. Overview & Goals
*Why it's critical: reviewers need to know what "done" looks like before evaluating whether the design achieves it.*

- **Problem statement:**
- **Goals (in scope):**
- **Non-goals (explicitly out of scope):**

---

## 2. Requirements

| Requirement | Type | Priority |
|---|---|---|
| | Functional/Non-Functional | Must/Should/Could |

**Non-Functional targets:**

| NFR | Target |
|---|---|
| Latency (p95) | |
| Throughput | |
| Availability | |

---

## 3. High-Level Design
*Why it's critical: this is what most reviewers actually read closely — get the shape of the solution agreed here before anyone reviews line-level detail.*

- **Diagram reference:** (`./evidence/high-level-design.png`)
- **Summary of approach:**

---

## 4. Detailed Design

### 4.1 API Contracts

| Endpoint | Method | Request | Response | Auth |
|---|---|---|---|---|
| `/api/x` | POST | `{...}` | `{...}` | Bearer token |

### 4.2 Data Model

| Field | Type | Constraints | Notes |
|---|---|---|---|
| | | | |

### 4.3 Sequence of Operations
*Why it's critical: race conditions and ordering bugs are far cheaper to catch here than in code review or production.*

```
1. Client → API: request
2. API → Service: validate + process
3. Service → DB: write
4. API → Client: response
```

---

## 5. Error Handling & Edge Cases

| Scenario | Expected Behavior | Error Code/Response |
|---|---|---|
| Invalid input | | 400 |
| Downstream service timeout | | 504 + retry policy |
| Concurrent write conflict | | |

---

## 6. Security Considerations
*Why it's critical: security bolted on after implementation is dramatically more expensive than designed in — this section forces the check at the cheapest possible point.*

| Concern | Approach |
|---|---|
| AuthN/AuthZ | |
| Input validation | |
| Data exposure (PII in logs/responses) | |
| Rate limiting/abuse prevention | |

---

## 7. Testing Strategy

| Test Type | Coverage Target | Approach |
|---|---|---|
| Unit | | |
| Integration | | |
| Load/Performance | | |
| Security (SAST/DAST) | | |

---

## 8. Rollout Plan

| Phase | Description | Rollback Trigger |
|---|---|---|
| Feature flag / canary | % of traffic | Error rate > X% |
| Full rollout | | |

---

## 9. Alternatives Considered

| Alternative | Why Rejected |
|---|---|
| | |

---

## 10. Open Questions
*Why it's critical: surfaces unresolved risk explicitly rather than letting it hide inside an assumption nobody stated out loud.*

| Question | Owner | Resolution |
|---|---|---|
| | | Pending |

---

## 11. Appendix
- **A. Full diagrams**
- **B. Related ADRs / architecture docs**
- **C. Sign-off:** Author, Tech Lead, Security Reviewer