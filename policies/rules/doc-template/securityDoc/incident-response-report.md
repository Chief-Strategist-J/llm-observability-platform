> **How to use this template**
> One-line *"Why it's critical"* notes explain each section's purpose — strip them before external distribution.

---

# [Incident Name] — Incident Response Report

| Field | Value |
|---|---|
| Incident ID | |
| Classification | Confidential / TLP:RED |
| Status | Active / Contained / Resolved / Closed |
| Detected On | |
| Reported On | |
| Report Version | |
| Incident Commander | |
| Authors | |

---

## 1. Executive Summary
*Why it's critical: leadership and legal/PR need a one-page answer to "what happened, are we safe now, what does it cost us" without reading the technical body.*

- **What happened:** 2–3 sentences, plain language.
- **Current status:** Contained / Ongoing / Resolved.
- **Business impact:** downtime, data exposed, financial/regulatory exposure.
- **Immediate actions taken:**

| Severity (SEV) | Definition | Example |
|---|---|---|
| SEV-1 | Active breach, data loss, or full outage | Ransomware detonation, confirmed exfil |
| SEV-2 | Significant degradation or contained compromise | Single host compromised, contained |
| SEV-3 | Limited scope, no confirmed data impact | Malware caught by EDR, no lateral movement |
| SEV-4 | Suspicious activity, unconfirmed | Anomalous login flagged, under investigation |

---

## 2. Incident Overview & Classification

| Field | Value |
|---|---|
| Incident Type | Ransomware / BEC / Data Breach / DDoS / Insider / Other |
| Severity | SEV-1/2/3/4 |
| Affected Systems | |
| Affected Data (if any) | PII / PHI / Financial / IP / None confirmed |
| Attack Vector (initial) | Phishing / Exploited CVE / Credential theft / Misconfig / Unknown |
| Threat Actor (if attributed) | |
| Regulatory Notification Required? | Yes/No — which regulator, deadline |

---

## 3. Timeline of Events
*Why it's critical: this is the record regulators, insurers, and your own post-mortem will scrutinize most — every gap in the timeline is a gap in your defense.*

| Timestamp (UTC) | Event | Source | Actor/System |
|---|---|---|---|
| | First suspicious activity | | |
| | Detection alert fired | | |
| | Analyst triage began | | |
| | Containment action taken | | |
| | Incident declared / escalated | | |
| | Executive/legal notified | | |
| | Eradication complete | | |
| | Systems restored | | |

---

## 4. Detection & Analysis
*Why it's critical: documents how the incident was found and confirms the scope wasn't guessed — this is what "confirmed vs. suspected" impact is based on.*

- **Detection source:** SIEM alert / EDR / user report / third-party notification.
- **Indicators of Compromise (IOCs):**

| Type | Value | Context |
|---|---|---|
| IP | | C2 server / attacker source |
| Domain | | |
| File Hash | | Malware sample |
| Account | | Compromised credential |

- **Scope confirmation:** how "affected systems" list was validated (log review, forensic imaging, EDR sweep).

---

## 5. Containment Actions
*Why it's critical: containment decisions made under time pressure are exactly what gets second-guessed later — recording the reasoning protects the response team.*

| Action | System(s) | Taken By | Timestamp | Reasoning |
|---|---|---|---|---|
| Isolated host from network | | | | Prevent lateral movement |
| Disabled account | | | | Suspected compromised credential |
| Blocked IOC at firewall/proxy | | | | Cut C2 channel |

- **Short-term vs. long-term containment:** note which actions were temporary patches vs. durable fixes.

---

## 6. Eradication
*Why it's critical: incomplete eradication is the #1 cause of "the same incident happened again two weeks later."*

| Step | Description | Verified By | Verification Method |
|---|---|---|---|
| Malware/backdoor removal | | | Re-scan / hash comparison |
| Credential rotation | | | Forced reset confirmed |
| Patch/config fix applied | | | Vuln rescan |

---

## 7. Recovery
*Why it's critical: restoring service too early re-exposes the same vulnerability; this section is the evidence recovery was staged and monitored, not rushed.*

| System | Recovery Action | Restored On | Monitoring Post-Recovery |
|---|---|---|---|
| | Restored from clean backup / rebuilt | | Enhanced logging for 30 days |

---

## 8. Root Cause Analysis
*Why it's critical: without this, the org fixes the symptom (this one host) and not the cause (the process/tech gap that let it happen).*

| Root Cause | Category | Contributing Factors |
|---|---|---|
| | People / Process / Technology | e.g., missing MFA, delayed patching, no segmentation |

---

## 9. Impact Assessment

| Impact Area | Details | Confirmed / Estimated |
|---|---|---|
| Data Exposed | | |
| Downtime | | |
| Financial Cost | Response + remediation + potential fines | |
| Regulatory/Legal | Notifications required, deadlines | |
| Reputational | | |

---

## 10. Communications Log
*Why it's critical: for regulated incidents, who-knew-what-when is often legally material — this log is frequently requested in audits or litigation.*

| Timestamp | Audience | Channel | Message Summary | Sent By |
|---|---|---|---|---|
| | Executive team | Email/Call | | |
| | Customers | Public statement | | |
| | Regulator | Formal notice | | |

---

## 11. Lessons Learned / Post-Incident Review
*Why it's critical: the blameless retro is where the actual ROI of the incident lives — skipping it means paying the "cost" of the incident without buying any of the improvement.*

| What Went Well | What Didn't | Action Item |
|---|---|---|
| | | |

---

## 12. Recommendations & Action Items

| ID | Recommendation | Owner | Priority | Target Date | Status |
|---|---|---|---|---|---|
| A-01 | | | P0/P1/P2 | | Not Started |

---

## 13. Appendix / Evidence
- **A. Forensic images/log exports:** file references
- **B. Tools used:** EDR/SIEM/forensic tool versions
- **C. Related tickets/case numbers**
- **D. Sign-off:** Incident Commander, Legal, CISO