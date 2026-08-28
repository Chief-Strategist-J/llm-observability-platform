> **How to use this template**
> One-line *"Why it's critical"* notes explain each section's purpose — strip them before distribution.
> Difference from the Incident Response **Report**: a playbook is used **during** an incident to guide action in real time; the report documents what happened **after**. Keep this one skimmable under pressure — short sentences, checkboxes, no prose paragraphs.
> Duplicate this file per incident type (Ransomware, Phishing, DDoS, Insider Threat, Data Breach, Account Compromise) — don't try to make one playbook cover every scenario.

---

# [Incident Type] Response Playbook

| Field | Value |
|---|---|
| Playbook ID | |
| Incident Type | Ransomware / Phishing / DDoS / Insider Threat / Account Compromise / Data Breach |
| Owner Team | |
| Last Tested (tabletop/drill date) | |
| Last Updated | |

---

## 1. Trigger Conditions
*Why it's critical: tells the on-call person exactly when to invoke this playbook vs. treat it as a routine ticket — ambiguity here costs the most time in the first 15 minutes.*

- [ ] Condition A (e.g., EDR fires ransomware behavioral alert)
- [ ] Condition B (e.g., multiple users report encrypted files)
- [ ] Condition C (e.g., ransom note detected)

**Severity on trigger:** SEV-1 (default) — downgrade only after triage confirms limited scope.

---

## 2. Roles & Immediate Contacts

| Role | Name/Rotation | Contact | Responsibility |
|---|---|---|---|
| Incident Commander | | | Overall coordination, decisions |
| Technical Lead | | | Containment/eradication execution |
| Comms Lead | | | Internal/external communications |
| Legal/Compliance | | | Regulatory notification calls |
| Executive Sponsor | | | Business decisions (e.g., pay ransom, take systems offline) |

---

## 3. First 15 Minutes — Immediate Actions
*Why it's critical: this is the checklist the responder follows before thinking, not after — under stress, people default to a list, not judgment.*

- [ ] Confirm the trigger condition is real (not a false positive)
- [ ] Declare incident, assign Incident Commander
- [ ] Open incident channel/bridge (#incident-XXX)
- [ ] Start incident timeline log (timestamp everything from here)
- [ ] Isolate affected system(s) — **do not power off** (preserve memory for forensics) unless actively destructive
- [ ] Notify Technical Lead + Legal (do not wait for full scope confirmation)

---

## 4. Containment Steps

| Step | Action | Command/Tool | Verification |
|---|---|---|---|
| 1 | Isolate host from network | e.g., EDR network isolation | Confirm no outbound traffic |
| 2 | Disable compromised account(s) | IAM console/AD | Confirm login blocked |
| 3 | Block known IOCs at perimeter | Firewall/proxy rule | Confirm block active |
| 4 | Preserve evidence (memory/disk image) | Forensic imaging tool | Image hash recorded |

**Decision point:** if containment requires taking a production system offline, who approves? → [Executive Sponsor / Incident Commander]

---

## 5. Investigation Checklist

- [ ] Identify initial access vector
- [ ] Identify all affected systems/accounts
- [ ] Identify data accessed/exfiltrated (if any)
- [ ] Determine attacker dwell time
- [ ] Check for persistence mechanisms (scheduled tasks, new accounts, backdoors)

---

## 6. Eradication Checklist

- [ ] Remove malware/backdoors from all affected systems
- [ ] Rotate all potentially exposed credentials
- [ ] Patch exploited vulnerability
- [ ] Verify no residual attacker access (re-scan, review new-account/scheduled-task logs)

---

## 7. Recovery Checklist

- [ ] Restore from known-clean backup (verify backup predates compromise)
- [ ] Rebuild from gold image where restore isn't trustworthy
- [ ] Apply enhanced monitoring on recovered systems for [30] days
- [ ] Confirm business function restored and validated by system owner

---

## 8. Communication Templates
*Why it's critical: drafting these mid-incident wastes time and risks saying the wrong thing under pressure — pre-approved language should already exist.*

**Internal (Slack/Email) — initial notice:**
> We are currently responding to a [incident type]. [Systems affected] are [status]. Updates every [30 min] in #incident-XXX.

**Customer-facing (if required) — draft, requires Legal/Comms sign-off before sending:**
> [Placeholder — do not send without approval]

**Regulatory notification (if applicable):** link to Legal's pre-approved template + reporting deadline for relevant regulation (e.g., 72 hrs under GDPR).

---

## 9. Decision Log
*Why it's critical: major calls (pay ransom? take prod offline? notify customers early?) get questioned after the fact — recording rationale at the time protects the team.*

| Timestamp | Decision | Made By | Rationale |
|---|---|---|---|
| | | | |

---

## 10. Stand-Down Criteria

- [ ] Threat contained and eradicated (verified, not assumed)
- [ ] All affected systems recovered and monitored
- [ ] Incident Commander formally declares stand-down
- [ ] Handoff to Incident Response Report process (separate document)

---

## 11. Post-Playbook Actions
- [ ] Complete full Incident Response Report (separate template)
- [ ] Schedule blameless post-mortem within [5 business days]
- [ ] Update this playbook with lessons learned

---

## 12. Appendix
- **A. Tool access list** (who has access to EDR/SIEM/IAM consoles during an incident)
- **B. Escalation matrix reference** (see RACI/Escalation Matrix doc)
- **C. Vendor/external support contacts** (forensics firm, cyber insurance hotline, law enforcement)