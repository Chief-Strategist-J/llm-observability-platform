> **How to use this template**
> Checklists are the lightweight, constantly-reused counterpart to the full reports/reviews — meant to be run every time, not filed once. Keep them short enough that people actually complete them.

---

# 1. Pre-Deployment Security Checklist
*Why it's critical: this is the last gate before production — a missed item here ships directly to users/attackers.*

**Application:** _______  **Version:** _______  **Date:** _______  **Checked By:** _______

### Authentication & Authorization
- [ ] MFA enforced for privileged accounts
- [ ] Default credentials changed/disabled
- [ ] Session timeout configured appropriately
- [ ] Authorization checks present on all sensitive endpoints (not just UI-hidden)

### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] TLS enforced for all data in transit
- [ ] No secrets/keys hardcoded in source or config committed to repo
- [ ] PII/sensitive fields excluded from logs

### Input Handling
- [ ] Input validation on all user-supplied data
- [ ] Parameterized queries used (no string-concatenated SQL)
- [ ] File upload restrictions in place (type, size, storage location)

### Infrastructure
- [ ] Unused ports/services disabled
- [ ] Security groups/firewall rules reviewed (least privilege)
- [ ] Dependencies scanned for known vulnerabilities (SCA tool run)
- [ ] Secrets stored in vault/KMS, not environment files in repo

### Monitoring
- [ ] Logging enabled for security-relevant events
- [ ] Alerting configured for anomalies (failed logins, error spikes)
- [ ] Rollback plan documented and tested

**Sign-off required from:** Security reviewer + Engineering lead before deployment.

---

# 2. Secure Code Review Checklist
*Why it's critical: catches the classes of bug that automated scanners consistently miss (business logic flaws, broken access control).*

**PR/Repo:** _______  **Reviewer:** _______  **Date:** _______

- [ ] Authorization enforced server-side (not just client-side/UI)
- [ ] No sensitive data in logs, error messages, or comments
- [ ] Input validated and output encoded (XSS/injection prevention)
- [ ] Error handling doesn't leak stack traces/internal details to users
- [ ] New dependencies checked for known CVEs and license compliance
- [ ] Secrets not committed (scan with pre-commit hook / secret scanner)
- [ ] Rate limiting applied to new public-facing endpoints
- [ ] Tests cover negative/abuse cases, not just happy path

---

# 3. Third-Party / Vendor Security Checklist
*Why it's critical: vendor compromise is a top breach vector — this should run before signing, not after onboarding.*

**Vendor:** _______  **Data Shared:** _______  **Date:** _______

- [ ] Vendor security questionnaire completed
- [ ] SOC 2 / ISO 27001 report reviewed (or equivalent)
- [ ] Data processing agreement (DPA) signed if handling PII
- [ ] Data classification of shared data documented
- [ ] Access revocation process defined for contract end
- [ ] Incident notification clause in contract (vendor must notify us within X hours of their breach)

---

# 4. Cloud Resource Provisioning Checklist
*Why it's critical: the majority of cloud breaches trace back to a misconfiguration made at provisioning time — this catches it before it's live.*

**Resource:** _______  **Environment:** _______  **Date:** _______

- [ ] No public access on storage buckets/databases unless explicitly required and approved
- [ ] IAM role follows least privilege (no wildcard permissions)
- [ ] Encryption enabled by default
- [ ] Logging/monitoring enabled (CloudTrail/Activity Log)
- [ ] Tagged for cost/ownership tracking
- [ ] Included in backup policy if stateful

---

## Appendix
- **A. Checklist owner/maintainer:** who updates these as new threats emerge
- **B. Frequency:** pre-deployment (every release), code review (every PR), vendor (every new vendor + annual re-review), cloud provisioning (every new resource)