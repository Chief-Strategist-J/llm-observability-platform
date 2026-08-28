> **How to use this template**
> Each section has a one-line *"Why it's critical"* note explaining its purpose — delete these notes before sending the final report externally. Tables are the standard where they exist; don't collapse them back into prose, since prose tables are what makes reports hard to skim under time pressure.

---

# [Engagement Name] — Security Assessment Report

| Field | Value |
|---|---|
| Report ID | |
| Classification | Confidential / TLP:AMBER |
| Version | 1.0 |
| Engagement Type | Red Team / Penetration Test / Purple Team |
| Assessment Dates | |
| Report Date | |
| Authors | |
| Reviewed By | |
| Distribution List | |

---

## 1. Executive Summary
*Why it's critical: this is the only section leadership reads in full — it must stand alone and drive a decision (fund remediation, accept risk, escalate).*

- **Objective:** one paragraph — what was tested and why.
- **Overall Risk Posture:** Critical / High / Moderate / Low (pick one, justify in 1–2 sentences).
- **Key Business Impact:** what could actually happen (data loss, fraud, downtime) — no jargon.

| Severity | Count | Notable Example |
|---|---|---|
| Critical (P0) | | |
| High (P1) | | |
| Medium (P2) | | |
| Low (P3) | | |

---

## 2. Scope & Rules of Engagement
*Why it's critical: defines legal authorization and the boundary of what was — and wasn't — tested. Protects both sides and tells the reader what "not found" actually means.*

| Item | Detail |
|---|---|
| In-Scope Assets | IP ranges, domains, applications, physical sites |
| Out-of-Scope Assets | explicitly excluded systems |
| Testing Type | Black-box / Grey-box / White-box |
| Testing Window | dates & hours (business hours vs. after-hours) |
| Source IPs Used | |
| Authorized By | name, role, date signed |
| Emergency Contact | name, phone, escalation path |
| Rules | e.g., no DoS, no social engineering of execs, stop conditions |

---

## 3. System / Attack Surface Overview
*Why it's critical: gives the reader the mental map needed to understand where findings sit and how exposed the target actually is.*

- **Architecture summary:** brief description or diagram reference (`./evidence/architecture.png`).
- **Asset inventory:**

| Asset | Type | IP/URL | Exposure | Criticality |
|---|---|---|---|---|
| | Web App / API / Host / Cloud Svc | | Internet-facing / Internal | High/Med/Low |

- **Identity & trust boundaries:** auth mechanisms, network segmentation notes, third-party integrations.

---

## 4. Methodology
*Why it's critical: establishes credibility and repeatability — shows the assessment was systematic, not ad hoc, and lets a future team reproduce or extend it.*

| Phase | Activities | Framework Reference |
|---|---|---|
| Reconnaissance | OSINT, asset discovery | PTES / OWASP Testing Guide |
| Enumeration | Service/version fingerprinting | |
| Vulnerability Analysis | Scanning, manual review | CWE, CVE |
| Exploitation | Controlled PoC exploitation | MITRE ATT&CK (map TTPs) |
| Post-Exploitation | Privilege escalation, lateral movement | MITRE ATT&CK |
| Reporting | Findings, risk scoring | CVSS v3.1/v4 |

- **Tools used:** list tool name + version (for reproducibility).
- **Constraints encountered:** anything that limited coverage (blocked IPs, WAF, time-box).

---

## 5. Findings
*Why it's critical: this is the technical core — everything downstream (remediation, retest, risk acceptance) traces back to a specific finding here. Inconsistent structure here is what makes reports hard to act on.*

### 5.1 Severity Definitions

| Severity | CVSS Range | Definition | SLA to Fix |
|---|---|---|---|
| P0 – Critical | 9.0–10.0 | Immediate compromise of confidentiality/integrity/availability at scale (e.g., RCE, auth bypass) | 24–72 hrs |
| P1 – High | 7.0–8.9 | Significant impact, likely exploitable with moderate effort | 7–14 days |
| P2 – Medium | 4.0–6.9 | Limited impact or requires specific conditions/chaining | 30 days |
| P3 – Low | 0.1–3.9 | Informational / defense-in-depth / best-practice gap | 90 days |

### 5.2 Findings Summary Table

| ID | Title | Severity | CVSS | Affected Asset | Status |
|---|---|---|---|---|---|
| F-001 | | | | | Open/Fixed/Accepted |

### 5.3 Finding Detail Template (repeat per finding)

#### F-00X: [Finding Title]

| Field | Value |
|---|---|
| Severity | P0/P1/P2/P3 |
| CVSS Vector | AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H |
| CWE / CVE | |
| Affected Asset(s) | |
| MITRE ATT&CK Technique | |

**Description**
What the vulnerability is, in plain technical terms.

**Evidence**
Screenshots, request/response pairs, logs — reference file paths (`./evidence/F-001-req.png`). Redact sensitive data.

**Exploitability**
- Preconditions required (auth level, network position, user interaction)
- Attack complexity: Low/Medium/High
- Reliability: does it work every time, or is it flaky?

**Impact**
Business-level consequence if exploited (not just "RCE" — what does RCE *mean* here: data exfil, ransomware pivot, fraud, etc.)

**Reproduction Steps**
1. Step-by-step, numbered, tool-agnostic where possible
2. Include exact payloads/commands used
3. Expected result at each step

**Recommendation**
Short-term mitigation vs. long-term fix (link to Section 8 remediation ID).

---

## 6. Attack Chains
*Why it's critical: individual findings are often "medium" in isolation but "critical" when chained — this section is where the real business risk usually lives, and it's the part most templates omit.*

### Chain Narrative
Describe the end-to-end path an attacker took, referencing finding IDs in sequence.

| Step | Finding ID | Action | MITRE Tactic |
|---|---|---|---|
| 1 | F-003 | Initial foothold via | Initial Access |
| 2 | F-007 | Privilege escalation via | Privilege Escalation |
| 3 | F-012 | Lateral movement to | Lateral Movement |
| 4 | F-015 | Data exfiltration / objective achieved | Exfiltration |

**Kill Chain Diagram:** reference (`./evidence/attack-chain.png`).

---

## 7. Root Cause Analysis
*Why it's critical: without this, teams patch symptoms one-by-one and the same class of bug reappears next quarter. This is what turns a report into a process improvement.*

| Root Cause Category | Findings Affected | Systemic Issue |
|---|---|---|
| People (training/awareness) | | |
| Process (SDLC, patch mgmt, change control) | | |
| Technology (architecture, config, legacy) | | |

**Recurring Themes:** e.g., "input validation missing across 6 of 9 API endpoints" — patterns matter more than individual bugs.

---

## 8. Remediation
*Why it's critical: converts findings into assigned, trackable work — this is the section that actually gets used day-to-day by engineering/IT, not just read once.*

| Finding ID | Recommendation | Owner | Priority | Effort (S/M/L) | Target Date | Status |
|---|---|---|---|---|---|---|
| F-001 | | | P0 | | | Not Started |

**Compensating Controls (if fix is delayed):** WAF rules, monitoring alerts, network ACLs, etc.

---

## 9. Validation / Retest
*Why it's critical: an unverified fix is not a fix — this closes the loop and is often contractually required before an audit/compliance sign-off.*

| Finding ID | Retest Date | Method | Result | Retested By |
|---|---|---|---|---|
| F-001 | | Manual re-exploitation / scan | Fixed / Not Fixed / Partially Fixed | |

---

## 10. Residual Risk
*Why it's critical: documents what remains unfixed and who formally accepted that risk — protects the security team and creates an audit trail.*

| Finding ID | Reason Not Fixed | Risk Accepted By | Review Date |
|---|---|---|---|
| | Business constraint / False positive / Compensating control in place | Name, Title | |

---

## 11. Appendix / Evidence
*Why it's critical: keeps the main body readable while preserving the raw proof an auditor, insurer, or skeptical engineer may ask for.*

- **A. Evidence Index:** file/folder mapping to each finding ID
- **B. Tools & Versions:** full list with configs used
- **C. Glossary:** acronyms and terms used in the report
- **D. Raw Scan Output:** linked, not pasted inline
- **E. Sign-off:** names/signatures of report author, technical reviewer, and client acceptance