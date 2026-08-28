# ADR-0006 Infrastructure Resilience — Security Assessment Report

| Field | Value |
|---|---|
| Report ID | SAR-LLMOBS-INFRA-AUD-0006 |
| Classification | Confidential |
| Version | 2.0.0 |
| Engagement Type | Independent Architecture, Security & Performance Audit |
| Assessment Dates | August 28, 2026 |
| Report Date | August 28, 2026 |
| Target Document | `packages/configs/llm-obs-infra/docs/architectureDoc/infrastructure-resilience-and-edge-case-hardening.md` |
| Authors | Independent Security & Systems Architecture Reviewer |
| Reviewed By | Infrastructure Steering Committee |
| Remediation Link | [remediation-plan-adr-0006.md](./remediation-plan-adr-0006.md) |

---

## 1. Executive Summary

This independent security assessment evaluates the technical claims, resilience hardening, security posture, and compliance statements made in **ADR-0006 (Infrastructure Resilience & Edge-Case Hardening)** for `packages/configs/llm-obs-infra`.

- **Objective:** Assess the 9-container stack topology, pre-flight checks, memory ceilings, redaction pipeline, and compliance claims (SOC2, ISO 27001, GDPR, HIPAA, EU AI Act) against production engineering standards.
- **Overall Risk Posture:** Moderate with Significant Security & Capacity Gaps. While ordered container startup, log rotation, and distroless `/dev/tcp` health probing represent solid tactical fixes, systemic overclaims exist regarding Zero-Trust network security and production memory limits.
- **Key Business Impact:** Potential unredacted API key exposure over internal HTTP plaintext hops, missing authentication on workflow engine ports, and pre-flight memory gate under-sizing that permits OOM panics under concurrent load.

| Severity | Count | Notable Example |
|---|---|---|
| Critical (P0) | 3 | Static network header signature non-functional as Zero-Trust control; Plaintext internal hop pre-redaction; Pre-flight memory gate 6x undersized. |
| High (P1) | 4 | Redaction missing event bodies/resource attributes; Unauthenticated Temporal engine; Single-node Kafka data-loss risk; Missing DR backup pipeline. |
| Medium (P2) | 6 | Redis password lacking ACL scoping; Audit log erasable by DB admin user; Unauthenticated internal service writes; Process termination without container ownership verification. |
| Low (P3) | 4 | Insecure `curl -k` TLS probe flag; Indefinite retry polling loops; ClickHouse missing concurrent query ceiling; Durability gap on FD limits. |

---

## 2. Scope & Rules of Engagement

| Item | Detail |
|---|---|
| In-Scope Assets | 9 Core Container Services (`llmobs-network`), `system-prereqs.sh`, `port-manager.sh`, `stack-orchestration.sh`, OTel Collector configs |
| Out-of-Scope Assets | External cloud provider billing API accounts |
| Testing Type | Grey-box Static Code & Architectural Verification Review |
| Testing Window | August 28, 2026 |
| Rules | Audit based on stated execution paths, port maps, cgroup resource limits, and script source verification |

---

## 3. System / Attack Surface Overview

The target system comprises 9 microservices running on private bridge `llmobs-network` (`172.28.0.0/16`) with host interface ports isolated to `31410–31425`.

| Asset / Container | Type | IP / Port | Exposure | Criticality |
|---|---|---|---|---|
| `llmobs-traefik` | Gateway | `:31410`, `:31419`, `:31411` | External Ingress | High |
| `llmobs-kafka` | Event Stream | `:31414` (Host), `:9092` (Internal) | Internal Stream | High |
| `llmobs-otel-collector` | Ingest Pipeline | `:31417` (HTTP), `:31418` (gRPC) | Ingress Receiver | Critical |
| `llmobs-clickhouse` | Analytics DB | `:8123` (HTTP), `:9000` (Native) | Internal DB | High |
| `llmobs-alloydb` | Metadata DB | `:31420` (Host), `:5432` (Internal) | Internal DB | High |
| `llmobs-redis` | Spend Ledger | `:31413` (Host), `:6379` (Internal) | Internal Cache | High |
| `llmobs-temporal` | Workflow Engine | `:7233` (gRPC), `:8088` (UI) | Orchestration | High |
| `llmobs-tempo` | Trace Store | `:31416` (Host), `:4317` (gRPC) | Internal Store | Medium |
| `llmobs-grafana` | Portal UI | `:31415` (Host 3000) | Dashboard | Medium |

---

## 4. Methodology

- **Framework References:** NIST SP 800-53, CIS Docker Benchmarks, OWASP ASVS v4.0, STRIDE Threat Modeling.
- **Analysis Phases:** 
  1. Architecture & Memory Gate Calculations.
  2. Ingress & Internal Network Trust Boundary Review.
  3. Redaction Engine & Payload Surface Audit.
  4. Database Security, Audit Integrity & Recovery Review.

---

## 5. Findings

### 5.1 Severity Definitions

| Severity | CVSS Range | Definition | SLA to Fix |
|---|---|---|---|
| P0 – Critical | 9.0–10.0 | Immediate compromise of confidentiality, integrity, or system availability | 24–72 hrs |
| P1 – High | 7.0–8.9 | Significant security or data-loss impact | 7–14 days |
| P2 – Medium | 4.0–6.9 | Moderate impact or operational vulnerability requiring specific conditions | 30 days |
| P3 – Low | 0.1–3.9 | Informational or defense-in-depth best-practice improvement | 90 days |

### 5.2 Findings Summary Table

| ID | Title | Severity | CVSS Vector | Affected Asset | Status |
|---|---|---|---|---|---|
| F-001 | Unauthenticated Network Signature Header | P0 - Critical | AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N | `llmobs-traefik` | Open |
| F-002 | Plaintext Internal Hop Pre-Redaction | P0 - Critical | AV:A/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N | `llmobs-otel-collector` | Open |
| F-003 | Memory Gate Undersized Relative to Stack Ceiling | P0 - Critical | AV:L/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H | `system-prereqs.sh` | Open |
| F-004 | Redaction Excludes Event Payload Bodies & Cloud Secrets | P1 - High | AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N | `otel-collector-config` | Open |
| F-005 | Unauthenticated Temporal Engine gRPC & Web UI | P1 - High | AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H | `llmobs-temporal` | Open |
| F-006 | Single Kafka Broker Data-Loss Risk (RF=1) | P1 - High | AV:L/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:H | `llmobs-kafka` | Open |
| F-007 | Missing Disaster Recovery & Volume Snapshot Pipeline | P1 - High | AV:L/AC:H/PR:N/UI:N/S:U/C:N/I:H/A:H | `db-backup-and-purge` | Open |
| F-008 | Shared Password Redis Auth Lacking ACL Scoping | P2 - Medium | AV:A/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N | `llmobs-redis` | Open |
| F-009 | Same-Database Self-Defeating Audit Log Integrity | P2 - Medium | AV:N/AC:L/PR:H/UI:N/S:U/C:N/I:H/A:N | `llmobs-alloydb` | Open |
| F-010 | Unauthenticated Service-to-Service Kafka & DB Writes | P2 - Medium | AV:A/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:N | `llmobs-kafka` | Open |
| F-011 | Unsafe Process Termination in `port-manager.sh` | P2 - Medium | AV:L/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H | `port-manager.sh` | Open |
| F-012 | Insecure `curl -k` Flag in Health Verification Probe | P3 - Low | AV:L/AC:H/PR:N/UI:N/S:U/C:L/I:L/A:N | `test-health.sh` | Open |

---

## 6. Attack Chains

### Chain 1: Internal Network Sniffing to API Key Exfiltration
1. Adversary achieves initial container foothold via a third-party dependency vulnerability (e.g. Grafana plugin CVE).
2. Adversary inspects bridge network traffic on `172.28.0.0/16`.
3. Inbound span payloads routed from Traefik to OTel Collector (`:4318`) transit over HTTP plaintext before redaction executes.
4. Adversary extracts unredacted `sk-...` API keys, Bearer tokens, and prompt context in flight.

---

## 7. Root Cause Analysis

| Root Cause Category | Findings Affected | Systemic Issue |
|---|---|---|
| Trust Boundary Assumption | F-001, F-002, F-010 | Internal container network treated as trusted without mTLS or service auth. |
| Memory Resource Oversight | F-003, F-006 | Pre-flight memory check evaluated container launch rather than peak load reservation floor. |
| Audit & Access Control | F-005, F-008, F-009 | Single shared credential pattern and same-database audit log placement. |

---

## 8. Remediation

Full technical remediation tasks, code snippets, target files, and checkboxes are specified in the accompanying [Remediation Plan](./remediation-plan-adr-0006.md).

---

## 9. Validation / Retest

| Finding ID | Retest Method | Target Result | Status |
|---|---|---|---|
| F-001 | Ingress header probe | Dynamic HMAC / mTLS verification | Pending |
| F-002 | Packet capture inspection | No unredacted keys on internal hop | Pending |
| F-003 | `./scripts/prereqs/system-prereqs.sh` | Gate requires >= 6,000MB free RAM | Pending |

---

## 10. Residual Risk

| Finding ID | Reason Not Immediately Fixed | Risk Accepted By | Review Date |
|---|---|---|---|
| Single Kafka Broker (F-006) | Acceptable for Single-Node Dev/Staging | Platform Tech Lead | Q4 2026 |

---

## 11. Appendix / Evidence

- **A. Evidence File Index**: Port map specifications (`REQUIREMENTS.md`), compose definitions (`docker-compose.yml`).
- **B. Tools & Versions**: OpenTelemetry Contrib Collector, Traefik v3.7, Apache Kafka KRaft, AlloyDB Omni 15.
- **C. Sign-off**: Independent Security Reviewer, Lead Systems Architect.
