> **How to use this template**
> One-line *"Why it's critical"* notes explain each section's purpose — strip them before external distribution.
> This assesses a system's *design* against security best practice/controls — it's proactive (before build/at design time or periodic review), unlike the pentest report which is reactive (after build, attacker's-eye view).

---

# [System Name] — Security Architecture Review

| Field | Value |
|---|---|
| Report ID | |
| Classification | Confidential |
| Review Type | Pre-deployment / Periodic / Post-incident-triggered |
| Review Date | |
| Reviewers | |
| System Owner | |

---

## 1. Executive Summary
*Why it's critical: this feeds a go/no-go or funding decision — leadership needs the verdict up front, not buried in section 6.*

- **Overall security posture:** Strong / Adequate with gaps / Significant gaps / Not ready.
- **Top 3 risks:**
- **Recommendation:** Approve / Approve with conditions / Do not proceed.

---

## 2. Scope of Review

| Item | Detail |
|---|---|
| System/Service Reviewed | |
| Architecture Version/Diagram Ref | |
| Review Boundary | which components in/out of scope |
| Standards Used | NIST 800-53 / ISO 27001 / CIS Benchmarks / OWASP ASVS |

---

## 3. Architecture Overview
*Why it's critical: you can't assess trust boundaries you haven't drawn — this is the shared mental model for the rest of the review.*

- **Diagram reference:** (`./evidence/architecture-diagram.png`)
- **Component inventory:**

| Component | Purpose | Technology | Data Classification Handled |
|---|---|---|---|
| | | | Public/Internal/Confidential/Restricted |

---

## 4. Trust Boundaries & Data Flow
*Why it's critical: most real-world breaches happen at a boundary crossing (internet→app, app→DB, service→service) — mapping them is where you find missing controls.*

| Boundary | Crossing Point | Data In Transit | Control Applied | Gap? |
|---|---|---|---|---|
| External → App | API Gateway | User PII | TLS 1.2+, WAF | |
| App → Database | Internal network | Credentials, records | mTLS / encryption at rest | |

---

## 5. Threat Surface Analysis

| Attack Surface | Exposure | Existing Mitigation | Residual Risk |
|---|---|---|---|
| Public API endpoints | Internet-facing | Rate limiting, auth | |
| Admin interfaces | VPN-only | MFA | |
| Third-party integrations | | | |

---

## 6. Control Assessment
*Why it's critical: maps design decisions to a recognized framework so gaps are auditable, not just "reviewer's opinion."*

| Control Domain | Control (NIST/CIS ref) | Status | Evidence |
|---|---|---|---|
| Identity & Access Management | Least privilege, MFA | Implemented / Partial / Missing | |
| Encryption | At-rest / in-transit | | |
| Logging & Monitoring | Centralized logging, alerting | | |
| Network Segmentation | | | |
| Secrets Management | Vault/KMS usage | | |
| Input Validation | | | |
| Secure SDLC | SAST/DAST/dependency scanning in CI/CD | | |

---

## 7. Gap Analysis

| Gap ID | Description | Related Control | Risk if Unaddressed | Severity |
|---|---|---|---|---|
| G-01 | | | | Critical/High/Med/Low |

---

## 8. Findings & Recommendations

| Finding ID | Recommendation | Design Change Required? | Owner | Priority | Target Date |
|---|---|---|---|---|---|
| G-01 | | Yes/No | | | |

---

## 9. Compliance Mapping
*Why it's critical: ties architecture decisions directly to regulatory/contractual obligations, which is usually what triggered the review in the first place.*

| Requirement | Regulation/Standard | Met? | Notes |
|---|---|---|---|
| Encryption of PII at rest | GDPR / PCI-DSS | Yes/No/Partial | |

---

## 10. Roadmap

| Phase | Changes | Timeline | Dependency |
|---|---|---|---|
| Immediate (pre-launch) | | | |
| Short-term (0–3 mo) | | | |
| Long-term (3–12 mo) | | | |

---

## 11. Appendix
- **A. Architecture diagrams (full resolution)**
- **B. Control framework checklist (full, e.g. CIS Controls v8)**
- **C. Interview/workshop notes**
- **D. Sign-off:** System Owner, Security Lead, Compliance