> **How to use this template**
> Policies are the rules everything else (reports, reviews, playbooks) gets measured against. Each is meant to be split into its own file once filled in — keep them together here only as a starting set. Legal/HR should review before these become binding.

---

# 1. Acceptable Use Policy (AUP)

| Field | Value |
|---|---|
| Policy ID | |
| Owner | |
| Approved By | |
| Effective Date | |
| Review Cycle | Annual |

### 1.1 Purpose
*Why it's critical: this is the document referenced in every HR/disciplinary action related to misuse — vague wording here is unenforceable wording.*
Defines acceptable use of company systems, devices, and data by employees/contractors.

### 1.2 Scope
Who this applies to (employees, contractors, third parties) and what systems it covers.

### 1.3 Policy Statements

| Area | Rule |
|---|---|
| Company devices | e.g., no personal use beyond incidental; no unauthorized software install |
| Internet/Email use | e.g., no accessing prohibited content categories; phishing report obligation |
| Personal devices (BYOD) | e.g., must enroll in MDM before accessing company data |
| Data handling | link to Data Classification Policy |
| Prohibited activities | e.g., installing unauthorized software, disabling security controls, sharing credentials |

### 1.4 Enforcement
Consequences of violation (reference to disciplinary policy/HR).

### 1.5 Exceptions
Process for requesting an exception and who approves it.

---

# 2. Access Control Policy

| Field | Value |
|---|---|
| Policy ID | |
| Owner | |
| Approved By | |
| Effective Date | |
| Review Cycle | Annual |

### 2.1 Purpose
*Why it's critical: this is the policy an auditor checks first — access control failures are the most common finding in SOC 2/ISO 27001 audits.*

### 2.2 Principles

| Principle | Statement |
|---|---|
| Least Privilege | Users granted minimum access needed for their role |
| Need-to-Know | Access to data limited to those who require it |
| Segregation of Duties | No single person controls an entire critical process |

### 2.3 Access Lifecycle

| Stage | Requirement |
|---|---|
| Onboarding | Access provisioned based on role (RBAC), approved by manager |
| Role Change | Access reviewed and adjusted within [X] business days |
| Offboarding | Access revoked within [X hours] of termination |
| Periodic Review | Access recertification every [quarter/6 months] |

### 2.4 Authentication Requirements

| Requirement | Standard |
|---|---|
| MFA | Required for all remote/privileged access |
| Password policy | Min length, complexity, rotation (if applicable), or passwordless standard |
| Privileged Access | Separate accounts for admin activity, session recording where applicable |

### 2.5 Exceptions & Approval
Process, approver, and maximum duration for temporary elevated access.

---

# 3. Data Classification Policy

| Field | Value |
|---|---|
| Policy ID | |
| Owner | |
| Approved By | |
| Effective Date | |
| Review Cycle | Annual |

### 3.1 Purpose
*Why it's critical: every other security control (encryption requirements, access control, retention) is defined *in terms of* classification level — get this wrong and downstream controls apply to the wrong data.*

### 3.2 Classification Levels

| Level | Definition | Example | Handling Requirement |
|---|---|---|---|
| Public | No harm if disclosed | Marketing materials | No restriction |
| Internal | Minor harm if disclosed externally | Internal docs, org charts | Internal access only |
| Confidential | Significant harm if disclosed | Financial data, contracts, source code | Encrypted at rest/transit, access logged |
| Restricted | Severe harm — legal/regulatory exposure | PII, PHI, payment data, credentials | Encrypted, access logged + monitored, DLP applied |

### 3.3 Handling Requirements by Level

| Control | Public | Internal | Confidential | Restricted |
|---|---|---|---|---|
| Encryption at rest | Optional | Recommended | Required | Required |
| Encryption in transit | Recommended | Required | Required | Required |
| Access logging | No | No | Yes | Yes + alerting |
| External sharing | Allowed | Approval required | Prohibited without DLP review | Prohibited |
| Retention | | | | Per regulatory requirement |

### 3.4 Labeling & Ownership
How data is tagged/labeled, and who is accountable as "data owner" per system/dataset.

### 3.5 Data Disposal
Requirements for secure deletion per classification level.

---

## Appendix (all policies)
- **A. Related policies:** Incident Response Policy, Password Policy, Third-Party Risk Policy
- **B. Definitions/Glossary**
- **C. Sign-off:** CISO, Legal, HR (as applicable)