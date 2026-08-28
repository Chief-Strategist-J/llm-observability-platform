# Critical Security Remediation Mandate — Adversarial Review of ADR-0006

| Field | Value |
| --- | --- |
| **ADR ID** | `ADR-SEC-REMEDIATION-0007` |
| **Title** | Critical Security Remediation Mandate — Adversarial Review of ADR-0006 |
| **Status** | **Proposed — BLOCKING** |
| **Date** | 2026-08-28 |
| **Reviewer Role** | Adversarial System Architecture & Security Review |
| **Amends** | [ADR-0006 — Infrastructure Resilience and Edge-Case Hardening](./infrastructure-resilience-and-edge-case-hardening.md) |
| **Scope** | `packages/configs/llm-obs-infra` — compose topology, gateway, datastores, deployment scripts, health suite, compliance tooling |
| **Verdict** | **NOT PRODUCTION-READY. Compliance claims in ADR-0006 §8 must be withdrawn until remediated.** |

---

## 1. Decision / Verdict

### Status: NOT PRODUCTION READY

ADR-0006 is an availability and ergonomics document wearing the vocabulary of a security document. It is competent at what it actually does — port allocation, cgroup limits, log rotation, startup ordering — and it is materially misleading everywhere it claims SOC 2, ISO 27001, GDPR, HIPAA, or EU AI Act posture.

Three structural problems make the ADR worse than no document at all:

1. **It documents controls that are not implemented.** `no-new-privileges:true` is named twice in ADR-0006. It appears zero times in `docker-compose.yml`. The "immutable audit log table" is a plain heap table in a `.sql` file that is never mounted and never executed. The "dual-write to ClickHouse" pipeline drawn in three separate diagrams has no ClickHouse exporter in the collector config.
2. **It presents the disabling of a security control as hardening.** Edge Case 13 records, as an achievement, that `curl` was given `-k` to stop certificate verification from failing. The recorded root cause — "self-signed RSA certificates cause `HTTP 000000`" — is the platform's TLS trust chain correctly reporting that it is untrustworthy. The fix silenced the alarm.
3. **Its evidence is a test suite engineered to pass.** The headline "52/52 HEALTH & SECURITY CHECKS PASSED" is not falsifiable. Container checks count `[WARN]` as a pass. The TLS check passes on a bare TCP connect. Header checks never inspect a header's value. The Redis auth check passes when the Redis container does not exist. Compose healthchecks end in `|| exit 0`. And `manage.sh` invokes the whole suite as `bash "$health_script" || true`. A green run is compatible with a completely broken, wide-open stack.

---

## 2. Executive Summary

### What Is Happening in Plain Terms?
Think of this infrastructure as a high-security building designed to store and monitor sensitive enterprise AI conversations and proprietary data. 

- **The Intended Design (ADR-0006):** Described an impenetrable bank vault with an armed front gate, security guards scanning every document for private information (credit cards, passwords, API keys), encrypted storage lockers, and an unforgeable visitor log.
- **The Actual Reality in Code (ADR-0007 Findings):** 
  1. **All Backdoors Left Wide Open:** While there is a front gate (Traefik gateway), every single internal storage room (databases, message queues, caches) has its own external door left unlocked and facing the public street (`0.0.0.0`), completely bypassing the security guard.
  2. **Keys Stored on the Bulletin Board:** The master keys and passwords to all databases are written down in public project files, and every time the system starts, it resets all locks back to these default public keys.
  3. **Fake Redaction & Shredding:** Private data is transported in clear view before it ever reaches the redaction filter, and the automated "data deletion/erasure" tool doesn't actually delete data—it silently ignores errors and claims success.
  4. **The Smoke Alarm Was Turned Off:** The automated testing suite was coded in a way where warning alarms and broken encryption checks are automatically marked as "PASSED", giving false peace of mind.

---

## 3. Critical Findings (P0) Breakdown

| Finding ID | Severity | Description | Target Scope |
|---|---|---|---|
| **P0-1** | Critical | Credentials published in git; `manage.sh` reinstalls them on every deploy | Environment configs |
| **P0-2** | Critical | All four datastore passwords committed in cleartext provisioning files | Grafana & ClickHouse configs |
| **P0-3** | Critical | SQL injection in the GDPR erasure utility, as database superuser | `gdpr-erasure.sh` |
| **P0-4** | Critical | GDPR erasure reports success unconditionally; targets tables that do not exist | `gdpr-erasure.sh` |
| **P0-5** | Critical | Every datastore published on `0.0.0.0`; UFW does not filter published ports | `docker-compose.yml` |
| **P0-6** | Critical | Unauthenticated Traefik API/dashboard, with the Docker socket mounted | Gateway config |
| **P0-7** | Critical | Redis dangerous commands unrestricted, no ACLs, no TLS, network-exposed | Redis config |
| **P0-8** | Critical | ClickHouse `default` has `access_management`, accepts `::/0`, `users.d` writable | ClickHouse config |
| **P0-9** | Critical | Kafka fully PLAINTEXT, no authentication or authorization, network-exposed | Kafka compose |
| **P0-10** | Critical | Traefik logs every request header upstream of PII redaction | Traefik access log |
| **P0-11** | Critical | `backup-purge` destroys all volumes; ClickHouse backup contains no data | Backup script |

---

## 4. Required Remediation Phases

### Phase 1 — Immediate Isolation (Target: 48 hours)
1. Rotate all database credentials and strip published defaults.
2. Remove host port publication for all internal datastores (`0.0.0.0` exposure).
3. Disable unauthenticated Traefik dashboard (`--api.insecure=true`).
4. Drop plaintext header logging in Traefik access logs.

### Phase 2 — Core Security Controls (Target: 2 weeks)
1. Implement Docker secrets for credential delivery.
2. Segment network bridge into `llmobs-edge` and `internal: true` `llmobs-data`.
3. Configure non-root user contexts (`user: 1000:1000`) and read-only filesystems.
4. Enable Kafka SASL_SSL and Redis ACL command denylists.

### Phase 3 — Audit & Governance Hardening (Target: 6 weeks)
1. Parameterize SQL queries in `gdpr-erasure.sh` and verify deletion row counts.
2. Mount and enforce append-only `security_audit_logs` relational table.
3. Configure fail-closed OTel PII redaction processors across all telemetry signals.
