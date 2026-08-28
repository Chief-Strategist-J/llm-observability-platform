> **How to use this template**
> One-line *"Why it's critical"* notes explain each section's purpose. This document answers two different questions — "who owns what" (RACI) and "who do I call right now" (escalation) — keep both, since one doesn't substitute for the other under time pressure.

---

# Security & Engineering RACI / Escalation Matrix

| Field | Value |
|---|---|
| Document ID | |
| Owner | |
| Last Updated | |
| Review Cycle | Quarterly (contacts go stale fast) |

---

## 1. RACI Legend

| Letter | Meaning |
|---|---|
| R | Responsible — does the work |
| A | Accountable — owns the outcome, signs off (only one A per row) |
| C | Consulted — input sought before decision |
| I | Informed — notified after the fact |

---

## 2. Security Activities RACI
*Why it's critical: the most common cause of dropped security work isn't lack of will, it's ambiguity about whose job it was — this table removes that ambiguity.*

| Activity | Security Team | Engineering | IT/Infra | Legal/Compliance | Executive |
|---|---|---|---|---|---|
| Vulnerability remediation | A | R | C | I | I |
| Incident response execution | R | R | C | C | A (SEV-1 only) |
| Security architecture review sign-off | A | C | C | I | I |
| Access provisioning/revocation | C | I | R/A | I | I |
| Third-party risk assessment | R | I | I | A | I |
| Policy approval | R | I | I | C | A |
| Penetration test scoping | A | C | C | I | I |
| Regulatory breach notification | C | I | I | A | R |

---

## 3. Escalation Matrix
*Why it's critical: this is the document people open at 2am — it needs to work without requiring them to think, search, or guess who's on call.*

| Severity | Initial Responder | Escalate To (if unresolved in) | Next Escalation | Executive Notification |
|---|---|---|---|---|
| SEV-1 (Critical) | On-call engineer | Incident Commander (immediate) | CISO (15 min) | CEO/CTO (30 min) |
| SEV-2 (High) | On-call engineer | Team Lead (30 min) | Incident Commander (1 hr) | CISO (2 hr) |
| SEV-3 (Medium) | Assigned engineer | Team Lead (next business day) | — | — |
| SEV-4 (Low) | Assigned engineer | — | — | — |

---

## 4. On-Call Contact Directory

| Role | Primary | Backup | Contact Method |
|---|---|---|---|
| Incident Commander (rotation) | | | Phone + PagerDuty |
| Security Lead | | | |
| Infrastructure Lead | | | |
| Legal/Compliance | | | |
| Executive Sponsor | | | |
| External: Forensics Firm | | | Retainer contract # |
| External: Cyber Insurance | | | Policy # |
| External: Law Enforcement (if applicable) | | | |

---

## 5. Decision Authority
*Why it's critical: certain calls (pay ransom, take prod offline, notify customers early) cannot wait for a meeting — this pre-assigns who is allowed to make them alone.*

| Decision | Who Can Approve Alone | Requires Two-Person Approval |
|---|---|---|
| Isolate a production system | Incident Commander | — |
| Pay ransom | — | CEO + Legal |
| Public customer notification | — | Comms Lead + Legal |
| Engage law enforcement | — | CISO + Legal |

---

## 6. Appendix
- **A. Change log:** who updated this doc and when (contacts/roles change often — track it)
- **B. Related documents:** Incident Response Playbooks, Incident Response Report template