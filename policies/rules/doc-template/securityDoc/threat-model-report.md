> **How to use this template**
> One-line *"Why it's critical"* notes explain each section's purpose — strip them before external distribution.
> This is a *design-time, structured brainstorm of what could go wrong* (STRIDE/DREAD) — narrower and earlier-stage than a full Security Architecture Review, usually done per-feature or per-service.

---

# [System/Feature Name] — Threat Model Report

| Field | Value |
|---|---|
| Report ID | |
| Classification | Confidential |
| Feature/System Version | |
| Threat Modeling Method | STRIDE / PASTA / Attack Trees |
| Date | |
| Participants | (should include eng lead + security) |

---

## 1. Executive Summary
*Why it's critical: engineering leads need the "must-fix-before-ship" list without reading the full threat enumeration.*

- **Feature/system summary:** one paragraph.
- **Highest-risk threats identified:**
- **Ship decision:** Ready / Ready with conditions / Blocked.

---

## 2. System / Feature Overview

| Field | Value |
|---|---|
| Description | |
| Users/Actors | who interacts with this system |
| Data Handled | classification level |
| Dependencies | upstream/downstream services |

---

## 3. Data Flow Diagram
*Why it's critical: STRIDE is applied per data flow / trust boundary — without a DFD, threats get identified inconsistently or missed entirely.*

- **Diagram reference:** (`./evidence/dfd.png`)
- **Elements identified:**

| Element | Type | Description |
|---|---|---|
| | External Entity / Process / Data Store / Data Flow | |

---

## 4. Trust Boundaries

| Boundary | Between | Why It's a Boundary |
|---|---|---|
| | User ↔ App | Different trust/privilege levels |
| | App ↔ Third-party API | Data leaves your control |

---

## 5. Threat Enumeration (STRIDE)
*Why it's critical: this is the core deliverable — each threat needs to be individually assessed, not lumped, or mitigations end up mismatched to the actual risk.*

| STRIDE Category | Applies To | Description |
|---|---|---|
| **S**poofing | | Identity impersonation |
| **T**ampering | | Unauthorized data/code modification |
| **R**epudiation | | Denying an action without traceability |
| **I**nformation Disclosure | | Unauthorized data exposure |
| **D**enial of Service | | Availability disruption |
| **E**levation of Privilege | | Gaining unauthorized access level |

### Detailed Threat Entries

| Field | Value |
|---|---|
| Threat ID | T-001 |
| STRIDE Category | |
| Affected Component/Flow | |
| Description | |
| Likelihood | High/Med/Low |
| Impact | High/Med/Low |
| DREAD Score (if used) | Damage/Reproducibility/Exploitability/Affected Users/Discoverability |
| Existing Mitigation | |
| Residual Risk | |

*(repeat per threat)*

---

## 6. Attack Trees
*Why it's critical: shows how individually "low" threats combine into a viable attack path — the same rationale as attack chains in a pentest report, but modeled before the system is built.*

```
Goal: Exfiltrate customer PII
├── Compromise API credentials
│   ├── Phishing employee (T-004)
│   └── Credential stuffing (T-007)
└── Exploit IDOR on /api/users/{id} (T-002)
```

---

## 7. Mitigation Plan

| Threat ID | Mitigation | Type (Design/Control/Accept) | Owner | Priority | Target Date |
|---|---|---|---|---|---|
| T-001 | | | | P0/P1/P2 | |

---

## 8. Residual Threats
*Why it's critical: formally records what risk ships with the system and who signed off — same purpose as residual risk in a pentest report, but recorded before launch rather than after a test.*

| Threat ID | Reason Not Mitigated | Accepted By | Review Date |
|---|---|---|---|

---

## 9. Appendix
- **A. Full DFD (all layers)**
- **B. Workshop notes / brainstorm raw list**
- **C. Related ADRs / design docs**
- **D. Sign-off:** Eng Lead, Security Reviewer