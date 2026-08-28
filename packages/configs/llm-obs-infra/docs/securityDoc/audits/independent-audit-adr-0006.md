# Independent Audit: ADR-0006 — Infrastructure Resilience & Edge-Case Hardening

| Field | Value |
|---|---|
| Target Document | `packages/configs/llm-obs-infra/docs/architectureDoc/infrastructure-resilience-and-edge-case-hardening.md` |
| Audit Role | System Architecture / Security / Performance Engineering Review |
| Audit Scope | Topology, Low-Level Design, Edge-Case Matrix, & Compliance Claims |
| Classification | Confidential / Internal |
| Date | 2026-08-28 |
| Remediation Plan | [remediation-plan-adr-0006.md](./remediation-plan-adr-0006.md) |

---

## 1. Executive Summary

The ADR documents a genuinely competent set of narrow, tactical fixes — ordered container startup, log rotation, `ulimit`/`sysctl` tuning, a clever `/dev/tcp` workaround for distroless health probing, and a correct root-cause fix for a curl status-code regex bug. Each of these, in isolation, is good engineering.

The problem is at the systems level. The document positions this collection of fixes as **"production-grade"** resilience and claims alignment with **SOC2, ISO 27001, GDPR, HIPAA, and the EU AI Act**. Neither claim survives scrutiny:

- **Performance:** the stack's own stated resource ceiling (~14.3GB) is roughly 6x the pre-flight memory gate (2.5GB) meant to protect against the exact OOM failure mode the ADR describes. Single-instance topology (one Kafka broker, one Collector, one of everything) means there is no horizontal scaling path and no replication — this is single-node dev/staging hardening, not production capacity engineering.
- **Security:** the flagship "Zero-Trust Network Signature" control is an unauthenticated, publicly-published static string with no verification step — it provides no actual protection. PII/secret redaction runs *after* a plaintext internal network hop, defeating its own purpose against any adversary already inside the bridge network. Temporal and internal Kafka have no described authentication at all.

None of this means the codebase is bad — it means the **ADR's framing overclaims relative to what's actually built**, and that gap is exactly what an external auditor, pen-tester, or enterprise security questionnaire will find first.

---

## 2. Architecture Recap (for reference)

9 containerized microservices on a single Docker bridge network (`llmobs-network`, `172.28.0.0/16`), ports isolated to `31410–31425`, 3-stage ordered startup (stateful DBs -> streams -> gateways/orchestration), fronted by Traefik with TLS termination, validated by a 52-check post-deploy health suite.

| Service | Role | Stated Resource Limit |
|---|---|---|
| Traefik | Edge TLS termination | 512MB |
| Redis | Rate-limit / cost ledger | 512MB |
| Kafka | Telemetry event stream | 2048MB limit / 512MB res / `-Xmx1024m` |
| ClickHouse | Columnar telemetry store | 4096MB limit / 1024MB res |
| Tempo | Trace store | 1024MB |
| OTel Collector | Ingestion pipeline | 1536MB limit / 256MB res |
| Grafana | Dashboards | 1024MB |
| AlloyDB (Postgres) | Relational metadata | 2048MB limit / 512MB res |
| Temporal | Workflow engine | 1536MB |

**Sum of stated limits: ~14,336MB. Sum of stated reservations: ~5,900MB.**  
**Pre-flight memory gate (`verify_system_memory`): >= 2,500MB free.**

---

## 3. Performance Engineering Findings

### 3.1 Pre-flight memory gate is ~6x undersized relative to the stack's own declared ceiling
`verify_system_memory(2500)` passes on any host with 2.5GB free RAM. The stack's own limits table sums to ~14.3GB worst case, ~5.9GB even at the reservation floor. A host that clears the pre-flight check by a comfortable margin (say, 4GB free) will still hit real memory contention under concurrent load — the exact OOM-cascade scenario Edge Case #4 claims to prevent. **The gate checks "can Docker start," not "can this stack run."**

**Fix:** gate against the sum of reservations at minimum, ideally limits + a 20% safety margin; fail pre-flight with the specific numbers if it doesn't clear.

### 3.2 Cgroup memory limits relocate the OOM failure, they don't eliminate it
A cgroup breach still delivers SIGKILL — now scoped to one container instead of the host, but the underlying risk (kill mid-write, mid-merge, mid-WAL-flush) is unchanged for that service. For ClickHouse specifically: a SIGKILL during a background MergeTree merge can leave orphaned/partial data parts requiring detached-parts cleanup or manual intervention on restart, with restart time no longer bounded.

**Gap:** no documented behavior for repeated OOM-kill (restart-loop detection, backoff, alerting). "52/52 checks passed" at idle startup says nothing about this.

**Fix:** document and test the OOM-kill -> restart -> recovery path explicitly per stateful service; add crash-loop alerting.

### 3.3 Kafka heap-to-container ratio is thin for the stated workload
`-Xmx1024m` inside a 2048MB limit leaves ~1GB for off-heap use, most of which functions as OS page cache — the primary performance lever for Kafka consumer catch-up and any replay/lag scenario. For a platform whose stated purpose is bursty telemetry ingestion, 1GB of page cache is likely to force disk-read fallback earlier than a "production-grade" claim implies.

**Gap:** no load-test evidence anywhere in the ADR — no throughput number, no p99 latency, no page-cache hit ratio, no GC pause data. Numbers without a load test are estimates presented as specifications.

**Fix:** run a representative load test (target spans/sec, sustained for N minutes) and publish the actual p50/p95/p99 latency and GC behavior before calling sizing "production-grade."

### 3.4 Single Kafka broker means replication factor <= 1 by construction
Combined with 3.2: an OOM-kill on the only broker holding the only replica of a partition, mid-write, is genuine unrecoverable data loss for whatever was in the unflushed segment. Edge Case #7 ("Storage Data Loss on Recreate") only protects against *container recreation* via named volumes — it does not protect against in-place crash loss, and the ADR conflates the two under one mitigation.

**Fix:** either explicitly scope this as single-node/non-HA in the ADR, or move to a minimum 3-broker Kafka topology with RF >= 2 for anything called "production-grade."

### 3.5 No stated deadline on the exponential-backoff polling loops
`wait_for_alloydb()`, `wait_for_clickhouse_http()`, `wait_for_web_gateways()` use backoff+jitter — correct pattern — but no maximum retry count or absolute timeout is documented. If a dependency never becomes healthy (corrupted WAL, disk full, bad migration), the deploy script's behavior is unspecified — likely an indefinite hang rather than a fast, loud failure.

**Fix:** hard ceiling (e.g., 5 minutes) with an explicit failure exit code and diagnostic dump, not indefinite retry.

### 3.6 The 52-check health suite is a t=0 idle snapshot, not a resilience proof
Every check runs once, immediately post-startup, against zero load. Nothing validates behavior under realistic ingestion volume: no stated throughput ceiling, no backpressure policy for what the OTel Collector does when Kafka/Tempo/ClickHouse can't keep up (drop spans? block upstream? hit its own 512MB `memory_limiter` and OOM itself?).

**Fix:** add a load-test stage to the validation suite distinct from the idle health check; document explicit backpressure/drop policy.

### 3.7 No horizontal scaling path for the ingestion path
One OTel Collector instance is the hard ceiling for the entire platform's ingestion throughput — every span from every instrumented application funnels through one process with a 1536MB limit. This is invisible in the architecture diagrams because they show logical flow, not instance count or scaling strategy.

**Fix:** document a collector replica strategy (behind Traefik, load-balanced) before claiming enterprise-scale readiness.

---

## 4. Security Findings

### 4.1 CRITICAL — The "Zero-Trust Network Signature" is not a security control
Per the ADR's own LLD: Traefik **injects** `X-LLMObs-Network-Signature: llmobs-net-sig-v1.0` into requests and **appends** it to responses. No described step verifies an inbound request's signature against an expected value and rejects on mismatch/absence. The value itself is a static string, published in this public ADR.

**Impact:** anyone — internal container, external attacker who reaches an exposed endpoint, or anyone who's read this document — can set that header themselves. It authenticates nothing. Citing this under **ISO 27001 origin verification** and calling it **"Zero-Trust"** is the single largest overclaim in the document and the first thing a real auditor or pen-tester will falsify.

**Fix:** replace with mTLS between services or SPIFFE/SPIRE-issued workload identity; if a header-based scheme is kept, it must be an HMAC over a per-request nonce/timestamp with a rotated secret, verified server-side, not a static label.

### 4.2 CRITICAL — Secrets transit the internal network in plaintext, before redaction runs
Traced from the ADR's own sequence diagram: TLS terminates at Traefik, then the next step is explicitly reverse proxy HTTP (plaintext) from Traefik to the OTel Collector on port 4318. PII/API-key redaction (`transform/pii_redaction`) does not execute until inside the Collector, **after** that plaintext hop.

**Impact:** any container on the flat `172.28.0.0/16` bridge — including one compromised via an unrelated dependency vulnerability (a Grafana plugin, a Kafka CVE, anything) — can capture unredacted `sk-...` API keys and Bearer tokens in flight, before the one control meant to protect them has run.

**Fix:** redact at the edge (in Traefik or at the Collector's receiver, before any internal hop) or encrypt the internal network (service mesh mTLS / IPsec / WireGuard overlay) so the plaintext hop is no longer a real exposure.

### 4.3 HIGH — Redaction coverage is narrow relative to what this system will actually see
Redaction engine iterates over the **span attribute map only**. OTel spans also carry **events** and **resource attributes**; logging pipelines carry **log record bodies** — none of these are stated as covered.

The four covered patterns — API key, Bearer token, email, credit card — miss the secret types most likely to actually appear in LLM prompt/response traffic: AWS keys (`AKIA...`), GCP service-account JSON, PEM private key blocks, JWTs, DB connection strings, GitHub/Slack tokens.

**Fix:** extend redaction to event bodies and resource attributes; expand the pattern set; add redaction-coverage tests with known-bad payloads in CI.

### 4.4 HIGH — Temporal has no described authentication
Temporal's frontend gRPC and Web UI (ports 31424/31425) default to open access unless explicitly configured with mTLS or an auth interceptor. The ADR's compliance section names auth enforcement only for "Redis and relational databases" — Temporal is never mentioned in that context.

**Impact:** if left at default, reaching port 31425 exposes full workflow execution history — plausibly including the same request/response payloads the rest of the architecture works to redact and protect.

**Fix:** enable Temporal's mTLS/auth interceptor explicitly; document it as a named control.

### 4.5 MEDIUM — Redis has authentication but no ACL scoping
"Password enforcement" implies a single shared credential, not Redis 6+ ACL-scoped service accounts. Redis here holds the **cost/billing ledger** — one leaked password grants full `FLUSHALL`/`CONFIG SET`/arbitrary-command access to financial state.

**Fix:** `ACL SETUSER` per consuming service, scoped to the specific key patterns and commands each service actually needs.

### 4.6 MEDIUM — Audit log integrity is self-defeating
`security_audit_logs` lives in the same AlloyDB instance and is presumably reachable by the same credentials that already have DDL/DML rights across that database. Anyone holding the Postgres admin password can `DELETE FROM security_audit_logs`.

**Fix:** ship audit events to append-only external storage (object storage with retention lock, or a separate DB with a distinct, more restricted credential).

### 4.7 MEDIUM — No internal service-to-service authentication beyond DB passwords
No SASL/mTLS is mentioned for Kafka producer/consumer auth — any container on the bridge network can produce/consume on any topic. No auth is mentioned on the Collector -> Tempo/ClickHouse write hops.

**Fix:** enable Kafka SASL_SSL with per-service credentials; authenticate the Collector's writes to Tempo/ClickHouse.

### 4.8 MEDIUM — `port-manager.sh` kills processes without ownership verification
`free_all_ports()` runs `fuser -k`/`kill -9` against any process bound to ports 31410–31425, with no check that the process belongs to a prior instance of this stack.

**Fix:** check the bound process's docker label or cgroup membership before killing; skip and warn instead of `kill -9` on anything unrecognized.

### 4.9 LOW — TLS verification is disabled in the tool meant to verify it
`check_http` uses `curl -sk` (`--insecure`) to work around self-signed cert failures. This suppresses certificate validation in the one place whose job is to confirm TLS is correctly configured.

**Fix:** pin the actual CA (`--cacert ca.pem`) instead of disabling verification.

---

## 5. Edge-Case Matrix — Verdict Per Item

| # | Edge Case | Verdict | Note |
|---|---|---|---|
| 1 | File descriptor limit | Pass (Script-Level) | Not persisted at systemd/host level — reverts on reboot without rerunning `manage.sh` |
| 2 | Kernel `vm.max_map_count` | Pass (Script-Level) | Same durability gap as #1 |
| 3 | Unbounded container logs | Pass (Stdout Only) | Unverified for app-level log files |
| 4 | Host-wide OOM cascades | Warning (Contained) | Contained to container, not eliminated |
| 5 | ClickHouse memory config | Pass (Split Correct) | Missing `max_concurrent_queries` ceiling |
| 6 | Kafka JVM heap | Warning (Undersized) | Likely undersized, unverified by load test |
| 7 | Storage data loss on recreate | Warning (Recreate Only) | Covers recreate only, not in-place crash |
| 8 | Host port collisions | Warning (Fixed Unsafely) | `kill -9` lacks ownership check |
| 9 | NTP desync | Warning (Active Check) | Checks "active," not "converged" |
| 10 | Distroless container probing | Pass (Probing Solved) | Correct workaround for missing `nc`/`curl` |
| 11 | DB recovery race condition | Pass (Pattern Correct) | Unverified against migration-timing edge case |
| 12 | Zero-Trust network signature | Fail (Non-Functional) | Not a functioning security control |
| 13 | HTTPS probe TLS/pattern match | Warning (Insecure Flag) | Status-code fix good; `-k` flag bad |
| 14 | Grafana datasource provisioning | Pass (Provisioned) | Standard secrets-in-env gap applies |

---

## 6. Compliance Claims — Reality Check

| Framework | ADR Claim | Actual Gap |
|---|---|---|
| **SOC2** | Privilege reduction, audit trail, TLS 1.2+ | Audit log is self-defeating (§4.6); privilege drop to `postgres`/`clickhouse` users is standard entrypoint behavior |
| **ISO 27001** | Network signature = origin verification | Signature is unauthenticated and unverified (§4.1) |
| **GDPR/CCPA** | PII redaction pipeline, erasure script | Redaction runs post-plaintext-hop and covers attributes only (§4.2–4.3) |
| **HIPAA** | Port isolation, DB auth | Port isolation isn't a recognized HIPAA control; no encryption-at-rest for AlloyDB/ClickHouse volumes |
| **EU AI Act** | Retains prompt/token data for auditability | Retention without stated retention policy works against EU AI Act data-minimization rules |

---

## 7. Prioritized Remediation Roadmap

### Tier 1 — Fix Core Value Proposition & False Claims
1. Move PII/secret redaction before the plaintext internal hop, or encrypt the internal network (§4.2).
2. Replace network "signature" with real mTLS/SPIFFE, or remove ISO 27001 claims against it (§4.1).
3. Add authentication to Temporal (§4.4) and internal Kafka (§4.7).

### Tier 2 — Close Real Operational & Data-Loss Risk
4. Fix pre-flight memory gate to check against actual reservation/limit sums (§3.1).
5. Confirm and test `gdpr-erasure.sh` covers every table holding user-linkable data (§4.6).
6. Add ownership checks to `port-manager.sh` before `kill -9` (§4.8).
7. Ship audit logs externally / append-only (§4.6).

### Tier 3 — Harden for Production Load
8. Run and publish an actual load test (throughput, p99 latency, GC behavior) (§3.3, §3.6).
9. Add scaling story for OTel Collector (§3.7) and/or move Kafka to a 3-broker RF >= 2 topology (§3.4).
10. Add hard timeouts to backoff/retry polling loops (§3.5).
11. Fix `check_http` to pin the CA instead of `-k` (§4.9).
12. Expand redaction coverage to event bodies/resource attributes (§4.3).

---

## 8. Summary Table — All Findings by Severity

| Severity | ID | Finding | Section |
|---|---|---|---|
| [Critical] | S1 | Network signature is unauthenticated, non-functional as a control | §4.1 |
| [Critical] | S2 | Redaction runs after a plaintext internal hop | §4.2 |
| [High] | S3 | Redaction coverage misses event bodies + most real-world secret types | §4.3 |
| [High] | S4 | Temporal has no described authentication | §4.4 |
| [Medium] | S5 | Redis shared password, no ACL scoping | §4.5 |
| [Medium] | S6 | Audit log erasable by the same credential it audits | §4.6 |
| [Medium] | S7 | No internal service-to-service auth (Kafka, store writes) | §4.7 |
| [Medium] | S8 | `port-manager.sh` kills processes without ownership check | §4.8 |
| [Low] | S9 | `curl -k` disables the one TLS verification step | §4.9 |
| [Critical] | P1 | Pre-flight memory gate ~4-6x undersized vs. real burst behavior | §3.1 |
| [High] | P2 | No DR/backup/restore story for any data store | §12 |
| [High] | P3 | Single Kafka broker = RF <= 1, no HA path | §3.4 |
| [Medium] | P4 | Cgroup OOM-kill relocates rather than eliminates crash risk | §3.2 |
| [Medium] | P5 | No horizontal scaling path for ingestion (Collector) | §3.7 |
| [Medium] | P6 | No throughput/latency numbers backing "production-grade" claim | §3.3 |
| [Low] | P7 | No deadline on backoff/retry polling loops | §3.5 |
| [Low] | P8 | No `max_concurrent_queries` ceiling on ClickHouse | §11.3 |
