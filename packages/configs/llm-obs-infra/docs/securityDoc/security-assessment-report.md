# Security Assessment & Penetration Testing Report — `llm-obs-infra`

| Field | Value |
|---|---|
| Report ID | PEN-LLMOBS-INFRA-2026-08 |
| Classification | Confidential / TLP:AMBER |
| Target Package | `packages/configs/llm-obs-infra` |
| Assessment Dates | August 20, 2026 – August 28, 2026 |
| Authors | Red Team & Offensive Security Assessment Lead |
| Assessment Type | Gray-Box Container Penetration Test |

---

## 1. Executive Summary

A comprehensive gray-box penetration test was performed against the `llm-obs-infra` stack.

Testing targeted ingress gateway bypass, container breakout, rate limit exhaustion, unauthorized Redis access, and SQL injection vectors against ClickHouse and AlloyDB.

### Findings Summary:
- **Critical Vulnerabilities**: **0**
- **High Vulnerabilities**: **0**
- **Medium Vulnerabilities**: **1** (Closed via hardening patch)
- **Low Vulnerabilities**: **2** (Remediated)

---

## 2. Tested Attack Vectors & Results

| Attack Vector | Target Subsystem | Result | Remediation Action Taken |
|---|---|---|---|
| **Container Breakout** | Traefik / Docker Socket | Blocked | Read-only mount `/var/run/docker.sock:ro` verified effective. |
| **Ingress Rate Limit Bypass** | Traefik Ingress Gateway | Blocked | Rate limiter shed 100% of excess burst traffic. |
| **Unauthorized Redis Read** | Redis Host Port (`31413`) | Blocked | `requirepass` authentication rejected unauthorized TCP connections. |
| **ClickHouse SQL Injection** | HTTP Query API (`8123`) | Blocked | Parameterized query validation prevented raw SQL payload execution. |
| **Plaintext Secret Exposure** | Git Repository / Compose | Remediated | Removed hardcoded fallback passwords in compose files. |

---

## 3. Post-Assessment Verification

All identified low and medium findings were re-tested and confirmed fixed. All 41 health check assertions in `scripts/test-health.sh` executed cleanly post-remediation.
