# llm-obs-infra Deployment Configuration — Critical Security Assessment Report

| Field | Value |
|---|---|
| Report ID | SAR-LLMOBS-INFRA-AUD-0007 |
| Classification | Confidential — Restricted Distribution |
| Version | 1.0.0 |
| Engagement Type | Independent Critical Security Audit (Implementation-Level) |
| Assessment Dates | August 28, 2026 |
| Report Date | August 28, 2026 |
| Target Scope | `packages/configs/llm-obs-infra` — deployed configuration, compose topology, service configs, operational scripts |
| Prior Audit | [independent-audit-adr-0006.md](./independent-audit-adr-0006.md) (documentation & architecture claims) |
| Authors | Independent Security & Systems Architecture Reviewer |
| Reviewed By | Infrastructure Steering Committee |
| Remediation Link | [remediation-plan-infra-deployment-config.md](./remediation-plan-infra-deployment-config.md) |

---

## 1. Executive Summary

AUD-0006 audited the **claims** made in ADR-0006. This audit (AUD-0007) audits the **shipped implementation** — `docker-compose.yml`, the nine service configuration files, the ten operational shell scripts, and the generated credential and TLS material actually present on disk. Where AUD-0006 findings were closed on paper, this audit re-tested them against code.

- **Objective:** Establish whether the deployed `llm-obs-infra` stack enforces the confidentiality, integrity, authentication, and compliance controls that the platform documentation asserts.
- **Overall Risk Posture:** **Critical — Not Fit for Production or Shared-Network Deployment.** The stack currently deploys with publicly-known credentials on every start, an unauthenticated gateway administration API bound to all host interfaces, the Docker socket mounted into that same gateway, full request headers (including `Authorization`) persisted to disk in cleartext, and an injectable GDPR erasure utility executing as database superuser.
- **Key Business Impact:** A single adversary with network reachability to the host — no credentials required — can obtain host root via the gateway/Docker-socket chain, read every stored LLM prompt, completion, API key, and customer identifier, forge trusted TLS certificates for all platform domains, and silently destroy the audit trail. Regulatory exposure spans GDPR Art. 17/32, SOC 2 CC6.1/CC6.6/CC7.2, ISO 27001 A.5.15/A.8.5/A.8.24, and PCI DSS 3.4/8.3 for any card data reaching the ingest path.
- **Most Consequential Systemic Defect:** `scripts/manage.sh` overwrites `.env` from the committed `.env.example` on **every** `npm run up`. Credential rotation is not merely absent — it is actively reverted on each deployment, and the credentials it restores are published in the repository.

| Severity | Count | Notable Example |
|---|---|---|
| Critical (P0) | 12 | Credential rotation reverted on every start; unauthenticated Traefik API on `0.0.0.0`; Docker socket in gateway container; all request headers logged in cleartext; SQL injection in GDPR erasure; world-readable CA and server private keys. |
| High (P1) | 12 | Audit-log schema and hardened `postgresql.conf` never mounted; healthchecks that cannot fail; filename-based script discovery executes arbitrary repo files; unattended `sudo` and firewall modification during `npm run up`; unencrypted backups containing superuser password hashes. |
| Medium (P2) | 10 | Mutable `latest` image tags; CA regenerated on every start; `port-manager.sh` `kill -9` of unrelated Docker processes; static "HMAC" headers presented as authentication; `curl -sk` with plaintext fallback in health verification. |
| Low (P3) | 5 | Audit table lacks tamper-evidence; production memory override inert; single shared certificate with `serverAuth,clientAuth` for all services. |
| **Total** | **39** | |

### 1.1 Re-Test of AUD-0006 Closures

Five AUD-0006 items marked `[x] Complete` do not hold at the implementation level.

| AUD-0006 Item | Claimed Status | AUD-0007 Verdict | Evidence |
|---|---|---|---|
| `CRIT-S1` Static network signature | Complete | **Fail** — still static; "secret" hardcoded in a tracked file | `config/traefik/dynamic.yml:27-34`, `scripts/test-health.sh:199` |
| `CRIT-S2` Plaintext internal hop | Complete | **Partial** — gateway hop is HTTPS but unverified; collector to Tempo hop still plaintext | `docker-compose.yml:34`, `config/otel-collector/otel-collector-config.yaml:86-87` |
| `HIGH-S3` Redaction coverage | Complete | **Partial** — `error_mode: ignore`, span events cover 3 of 7 patterns, no logs pipeline | `config/otel-collector/otel-collector-config.yaml:34-54` |
| `HIGH-S4` Temporal authentication | Complete | **Fail** — `TEMPORAL_AUTH_ENABLED` is not a Temporal variable; no `authorization:` block exists | `docker-compose.yml:311`, `config/temporal/temporal.yaml` |
| `F-011` Unsafe process termination | Complete | **Fail** — pattern still matches `dockerd`, `docker-proxy`, and all other projects' containers | `scripts/ports/port-manager.sh:17` |

---

## 2. Scope & Rules of Engagement

| Item | Detail |
|---|---|
| In-Scope Assets | `docker-compose.yml`, `docker-compose.prod.yml`, `.env`, `.env.example`, `config/{traefik,redis,kafka,clickhouse,alloydb,otel-collector,tempo,temporal,grafana,certs}/*`, `scripts/**/*.sh`, `backups/*`, `package.json` |
| Out-of-Scope Assets | Application packages (`packages/node/auth`, `packages/python/forecast-worker`), upstream container image CVEs, cloud provider accounts |
| Testing Type | White-box static configuration and shell source review, with on-disk artefact inspection (file modes, generated credentials, backup contents) |
| Testing Window | August 28, 2026 |
| Rules | No live exploitation performed. Findings derive from source inspection and filesystem state; each carries a file-and-line citation and a deterministic verification command. |
| Frameworks | CIS Docker Benchmark v1.6, NIST SP 800-53 Rev. 5, OWASP ASVS v4.0, OWASP Top 10 2021, CWE, STRIDE |

---

## 3. Attack Surface Overview

Host port bindings as published by `docker-compose.yml`. Every entry except the Temporal UI binds `0.0.0.0`, i.e. is reachable from any host on the local network segment.

| Host Binding | Service | Protocol | Authentication as Deployed | Exposure |
|---|---|---|---|---|
| `0.0.0.0:31410` | Traefik HTTP | HTTP | None (redirects to 443) | External |
| `0.0.0.0:31411` | **Traefik API / Dashboard** | HTTP | **None — `api.insecure=true`** | External |
| `0.0.0.0:31419` | Traefik HTTPS | HTTPS | None at edge | External |
| `0.0.0.0:31413` | Redis spend ledger | RESP | Password published in repo | LAN |
| `0.0.0.0:31414` | Kafka EXTERNAL | PLAINTEXT | **None — no SASL, no ACLs** | LAN |
| `0.0.0.0:31415` | Grafana | HTTP | Password published in repo | LAN |
| `0.0.0.0:31416` | Tempo query/stream | HTTP | **None** | LAN |
| `0.0.0.0:31417` | OTLP ingest HTTP | HTTPS | **None + CORS `*`** | LAN + any browser |
| `0.0.0.0:31418` | OTLP ingest gRPC | gRPC/TLS | **None** | LAN |
| `0.0.0.0:31420` | AlloyDB Omni | PostgreSQL | Superuser password published in repo | LAN |
| `0.0.0.0:31421` | ClickHouse HTTP | HTTP | Password published in repo, `::/0` allowed | LAN |
| `0.0.0.0:31422` | ClickHouse native | TCP | Password published in repo | LAN |
| `0.0.0.0:31423` | Tempo OTLP gRPC | gRPC | **None** | LAN |
| `0.0.0.0:31424` | **Temporal frontend gRPC** | gRPC | **None** | LAN |
| `127.0.0.1:31425` | Temporal Web UI | HTTP | None (localhost-bound) | Host only |

Additional trust-boundary observations: Traefik holds `/var/run/docker.sock`; Traefik carries `extra_hosts: host.docker.internal:host-gateway` and routes `/api/v1/auth` to `http://host.docker.internal:3001`, making the gateway a routing path onto host-local services.

---

## 4. Methodology

1. **Credential lifecycle trace** — followed every secret from `.env.example` through `setup.sh`, `manage.sh`, compose interpolation, and into each service config and script.
2. **Ingress and administration surface enumeration** — mapped published ports against the authentication actually configured in each service, not as documented.
3. **Container escape and privilege analysis** — reviewed socket mounts, capabilities, user context, and read-only posture against CIS Docker Benchmark.
4. **Data-plane confidentiality review** — traced telemetry from gateway ingress through redaction to storage, including logging sinks outside the redaction pipeline.
5. **Operational script review** — shell source audit for injection, unsafe `sudo`, destructive defaults, error suppression, and dynamic code execution.
6. **On-disk artefact inspection** — file modes on TLS material, backup contents, and `.env` versus `.env.example` equivalence.
7. **AUD-0006 closure re-test** — verified each item marked Complete against the code that supposedly implements it.

---

## 5. Findings

### 5.1 Severity Definitions

| Severity | CVSS Range | Definition | SLA to Fix |
|---|---|---|---|
| P0 — Critical | 9.0–10.0 | Immediate compromise of confidentiality, integrity, or availability; no or trivial preconditions | 24–72 hrs |
| P1 — High | 7.0–8.9 | Significant security or data-loss impact, or a control that is documented but absent | 7–14 days |
| P2 — Medium | 4.0–6.9 | Moderate impact, or requires specific conditions or local access | 30 days |
| P3 — Low | 0.1–3.9 | Defence-in-depth and hardening improvements | 90 days |

### 5.2 Findings Summary

| ID | Title | Severity | CWE | Affected Asset | Status |
|---|---|---|---|---|---|
| C-01 | Credential rotation reverted on every deployment | P0 - Critical | CWE-1188 | `scripts/manage.sh:40-46` | Open |
| C-02 | Secret generation in `setup.sh` is a silent no-op | P0 - Critical | CWE-1188 | `scripts/setup.sh:99-105` | Open |
| C-03 | Hardcoded credentials committed across tracked configs | P0 - Critical | CWE-798 | 7 tracked files | Open |
| C-04 | Unauthenticated Traefik API and dashboard on `0.0.0.0` | P0 - Critical | CWE-306 | `docker-compose.yml:21,40` | Open |
| C-05 | Docker socket mounted into internet-facing gateway | P0 - Critical | CWE-250 | `docker-compose.yml:43` | Open |
| C-06 | All request headers persisted to access logs in cleartext | P0 - Critical | CWE-532 | `docker-compose.yml:33` | Open |
| C-07 | SQL injection in GDPR erasure utility as superuser | P0 - Critical | CWE-89 | `scripts/gdpr-erasure.sh:60,74,78` | Open |
| C-08 | All data stores published on `0.0.0.0` with known credentials | P0 - Critical | CWE-668 | `docker-compose.yml` (ports) | Open |
| C-09 | Redis arbitrary-write / RCE path via unscoped `default` ACL | P0 - Critical | CWE-269 | `config/redis/redis.conf:12-19` | Open |
| C-10 | Temporal authentication non-functional; control plane open | P0 - Critical | CWE-1188 | `docker-compose.yml:311`, `config/temporal/temporal.yaml` | Open |
| C-11 | World-readable CA and server TLS private keys | P0 - Critical | CWE-732 | `scripts/generate-certs.sh:153`, `config/certs/` | Open |
| C-12 | Unauthenticated OTLP ingest with wildcard CORS | P0 - Critical | CWE-306 | `config/otel-collector/otel-collector-config.yaml:14-22` | Open |
| H-01 | Audit-log schema and hardened DB config never mounted | P1 - High | CWE-778 | `docker-compose.yml:286-287` | Open |
| H-02 | Healthchecks structurally incapable of failing | P1 - High | CWE-754 | `docker-compose.yml:80,124,291,332` | Open |
| H-03 | Filename-based discovery executes arbitrary repo scripts | P1 - High | CWE-427 | `scripts/discovery/dynamic-discovery.sh:141-190` | Open |
| H-04 | Unattended `sudo` and firewall change during `npm run up` | P1 - High | CWE-250 | `scripts/prereqs/system-prereqs.sh:19,29,54,88` | Open |
| H-05 | Credentials passed as command-line arguments | P1 - High | CWE-214 | `gdpr-erasure.sh`, `test-health.sh`, compose healthcheck | Open |
| H-06 | Kafka fully unauthenticated and unencrypted; config drift | P1 - High | CWE-306 | `docker-compose.yml:105-108`, `config/kafka/server.properties` | Open |
| H-07 | ClickHouse `default` user: `::/0` plus access management | P1 - High | CWE-269 | `config/clickhouse/users.d/default-user.xml:10-15` | Open |
| H-08 | Destructive default mode in backup utility | P1 - High | CWE-1188 | `scripts/db-backup-and-purge.sh:84` | Open |
| H-09 | Backups unencrypted, world-readable, contain password hashes | P1 - High | CWE-522 | `backups/` | Open |
| H-10 | TLS verification globally disabled between services | P1 - High | CWE-295 | `docker-compose.yml:34,37`, `dynamic.yml:145-147` | Open |
| H-11 | Redaction pipeline gaps and silent error suppression | P1 - High | CWE-390 | `config/otel-collector/otel-collector-config.yaml:34-54,97` | Open |
| H-12 | All containers run as root with full capabilities | P1 - High | CWE-250 | `docker-compose.yml` (all services) | Open |
| M-01 | Mutable `latest` tags and unpinned runtime plugin install | P2 - Medium | CWE-1357 | `docker-compose.yml:86,130,168,193,226,233` | Open |
| M-02 | Root CA and server key regenerated on every stack start | P2 - Medium | CWE-324 | `scripts/manage.sh:63` | Open |
| M-03 | `kill -9` of unrelated Docker and host processes | P2 - Medium | CWE-732 | `scripts/ports/port-manager.sh:17,26` | Open |
| M-04 | Unconditional removal of shared Docker network | P2 - Medium | CWE-1188 | `scripts/prereqs/system-prereqs.sh:124-135` | Open |
| M-05 | Static headers presented as HMAC authentication | P2 - Medium | CWE-1390 | `config/traefik/dynamic.yml:27-34` | Open |
| M-06 | `curl -sk` and plaintext fallback in health verification | P2 - Medium | CWE-295 | `scripts/test-health.sh` (8 sites) | Open |
| M-07 | Grafana datasources editable, AlloyDB `sslmode: disable` | P2 - Medium | CWE-732 | `config/grafana/provisioning/datasources/datasources.yml` | Open |
| M-08 | Gateway routing path onto host services; `sniStrict: false` | P2 - Medium | CWE-918 | `docker-compose.yml:52-53`, `dynamic.yml:15,169` | Open |
| M-09 | `.env` parsing truncates secrets containing `=` | P2 - Medium | CWE-20 | `gdpr-erasure.sh:50-52`, `test-health.sh:314,368,420` | Open |
| M-10 | Production override non-functional and security-inert | P2 - Medium | CWE-1188 | `docker-compose.prod.yml:16` | Open |
| L-01 | Audit table lacks tamper-evidence controls | P3 - Low | CWE-778 | `config/alloydb/security-audit.sql` | Open |
| L-02 | Production memory override inert against hardcoded ceiling | P3 - Low | CWE-770 | `config/clickhouse/config.d/custom.xml:20` | Open |
| L-03 | Version disclosure headers; deprecated XSS control; no CSP | P3 - Low | CWE-200 | `config/traefik/dynamic.yml:30-39` | Open |
| L-04 | Pervasive `|| true` masks failures under `set -e` | P3 - Low | CWE-390 | 4 scripts | Open |
| L-05 | Single shared certificate with `serverAuth,clientAuth` | P3 - Low | CWE-295 | `config/certs/openssl-san.cnf:18` | Open |

---

### 5.3 Critical Findings — Detail

#### C-01 — Credential Rotation Reverted on Every Deployment

| Field | Value |
|---|---|
| Severity | P0 — Critical |
| CVSS 3.1 | 9.8 — `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| CWE | CWE-1188 Insecure Default Initialization of Resource |
| Asset | `scripts/manage.sh:40-46`, invoked from `execute_up_pipeline` at `:55` |

`manage.sh` calls `ensure_env_file()` at the top of every `up` pipeline:

```bash
ensure_env_file() {
  local pkg_dir=$1
  if [ -f "$pkg_dir/.env.example" ]; then
    echo -e "${BLUE}Regenerating fresh .env file from .env.example...${NC}"
    cp -f "$pkg_dir/.env.example" "$pkg_dir/.env"
  fi
}
```

`cp -f` is unconditional. Any secret an operator rotates — by hand, by vault injection, or by CI — is destroyed on the next `npm run up` and replaced with the values committed to `.env.example`, which include `ALLOYDB_PASSWORD=llmobs_s3cret_2026`, `REDIS_PASSWORD=llmobs_redis_s3cret_2024`, `CLICKHOUSE_PASSWORD=llmobs_clickhouse_s3cret_2026`, and `GF_SECURITY_ADMIN_PASSWORD=llmobs_admin_password`.

**Verified state:** `diff .env .env.example` returns no differences. The live environment file is byte-identical to the committed template, confirming the overwrite has occurred and that the stack is running on repository-published credentials.

**Impact:** Every deployment of this stack — development, staging, and any production instance following the documented `npm run up` path — authenticates its database superuser, analytics store, spend ledger, and dashboard admin with credentials readable by anyone with repository access.

---

#### C-02 — Secret Generation in `setup.sh` Is a Silent No-Op

| Field | Value |
|---|---|
| Severity | P0 — Critical |
| CVSS 3.1 | 9.1 — `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N` |
| CWE | CWE-1188, CWE-703 Improper Check or Handling of Exceptional Conditions |
| Asset | `scripts/setup.sh:99-105` |

```bash
REDIS_PW=$(openssl rand -hex 16)
GRAFANA_PW=$(openssl rand -hex 16)
sed -i "s|REDIS_PASSWORD=<CHANGE_ME>|REDIS_PASSWORD=${REDIS_PW}|" "$PKG_DIR/.env"
sed -i "s|GF_SECURITY_ADMIN_PASSWORD=<CHANGE_ME>|GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PW}|" "$PKG_DIR/.env"
echo -e "  .env created with auto-generated secrets"
echo -e "    Redis password:   ${REDIS_PW}"
```

The `sed` expressions match the literal placeholder `<CHANGE_ME>`. **`.env.example` contains zero occurrences of `CHANGE_ME`** — it ships real passwords. Both substitutions therefore match nothing, `sed` exits 0, and `set -e` does not trigger. The script then prints two randomly generated passwords that were never written anywhere, and reports success.

**Impact:** The single documented mechanism for producing unique per-deployment secrets fails silently while emitting positive confirmation. Operators reasonably believe the stack is uniquely credentialed. This finding is the reason C-01 has gone unnoticed: the false success message conceals the overwrite.

---

#### C-03 — Hardcoded Credentials Committed Across Tracked Configuration

| Field | Value |
|---|---|
| Severity | P0 — Critical |
| CVSS 3.1 | 9.8 — `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| CWE | CWE-798 Use of Hard-coded Credentials |
| Asset | Seven git-tracked files |

`.env` and `config/certs/` are correctly excluded by `.gitignore`. The credentials, however, are committed elsewhere:

| File | Line | Secret |
|---|---|---|
| `config/grafana/provisioning/datasources/datasources.yml` | 27 | ClickHouse password in `secureJsonData` |
| `config/grafana/provisioning/datasources/datasources.yml` | 41 | AlloyDB `admin` password in `secureJsonData` |
| `config/grafana/provisioning/datasources/datasources.yml` | 50 | Redis password in `secureJsonData` |
| `config/redis/redis.conf` | 16-19 | Four ACL user passwords, including `worker_pass` and `limiter_pass` |
| `config/clickhouse/users.d/default-user.xml` | 13 | ClickHouse `default` password in CDATA |
| `scripts/gdpr-erasure.sh` | 63 | AlloyDB password as shell fallback default |
| `scripts/test-health.sh` | 469-471 | Two Redis passwords, repeated in three commands |
| `scripts/test-health.sh` | 199 | HMAC "secret key" `llmobs-net-sig-secret-key-v1.0` |
| `docker-compose.yml` | 69, 80, 150, 235, 279, 282, 309 | Interpolation fallbacks: `llmobs_redis_s3cret_2024`, `llmobs_redis_ledger_pass_2026`, `llmobs_clickhouse_s3cret_2026`, `admin`, `password` |

Two aggravating properties:

1. `docker-compose.yml:235` and `:279` fall back to `admin` and `password` respectively. If `.env` is absent, the stack starts with Grafana `admin:admin` and PostgreSQL superuser `admin:password`.
2. The `secureJsonData` field name in the Grafana provisioning file affords no protection at rest; it governs only how Grafana redacts the value in its own API responses.

These values are present in git history (`0883c34e`, `a3c990b0`) and must be treated as permanently disclosed. Rotation alone is insufficient — history rewriting or credential invalidation is required.

---

#### C-04 — Unauthenticated Traefik API and Dashboard on All Interfaces

| Field | Value |
|---|---|
| Severity | P0 — Critical |
| CVSS 3.1 | 9.1 — `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N` |
| CWE | CWE-306 Missing Authentication for Critical Function |
| Asset | `docker-compose.yml:21,40`; `config/traefik/traefik.yml:9-11` |

```yaml
command:
  - "--api.insecure=true"      # docker-compose.yml:21
ports:
  - "${PORT_TRAEFIK_DASHBOARD:-31411}:8080"   # bound to 0.0.0.0
```

`--api.insecure=true` serves the full Traefik API and dashboard on the `:8080` entrypoint with no authentication. The port is published without a host-interface restriction, so it answers on every interface of the host.

The `dashboard-router` in `dynamic.yml:91-99` attaches `security-headers` and `rate-limit` — but that router is bound to the `websecure` entrypoint only. Nothing is attached to `:8080`. The middleware provides no protection for the exposed path.

An unauthenticated request to `http://<host>:31411/api/rawdata` returns the complete runtime configuration: every router rule, every backend service URL, every middleware definition including the static header values, the TLS certificate store paths, and the resolved Docker provider inventory. `/debug/vars` and the Prometheus metrics endpoint are similarly reachable.

**Chained impact:** this is the entry point for the host-compromise chain described in Section 6, Chain 1, because the same container holds the Docker socket (C-05).

---

#### C-05 — Docker Socket Mounted Into the Internet-Facing Gateway

| Field | Value |
|---|---|
| Severity | P0 — Critical |
| CVSS 3.1 | 10.0 — `AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H` |
| CWE | CWE-250 Execution with Unnecessary Privileges |
| Asset | `docker-compose.yml:43` |

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

The `:ro` flag makes the socket *file* read-only; it does not restrict the Docker API reachable through it. The Docker Engine API exposes no read-only mode: a client that can write requests to the socket can `POST /containers/create` with `Binds: ["/:/host"]` and `Privileged: true`, then `POST /containers/{id}/start` — full root on the host filesystem. `:ro` prevents only `chmod`/`unlink` of the socket inode.

This capability is granted to the one container that is deliberately exposed to untrusted network traffic, and whose administration API is unauthenticated (C-04). Any Traefik vulnerability, any SSRF through the file provider, or direct dashboard-assisted reconnaissance converts to host root.

**CIS Docker Benchmark 5.31** explicitly prohibits mounting the Docker socket into containers. Traefik requires it only for the Docker provider; the file provider (`dynamic.yml`, already in use and covering every route) removes the requirement entirely.

---

#### C-06 — All Request Headers Persisted to Access Logs in Cleartext

| Field | Value |
|---|---|
| Severity | P0 — Critical |
| CVSS 3.1 | 9.1 — `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N` |
| CWE | CWE-532 Insertion of Sensitive Information into Log File |
| Asset | `docker-compose.yml:31-33`; `config/traefik/traefik.yml:27-31` |

```yaml
- "--accesslog=true"
- "--accesslog.format=json"
- "--accesslog.fields.headers.defaultmode=keep"
```

`defaultmode=keep` instructs Traefik to record **every** request header verbatim in each JSON access-log line. For an LLM observability gateway, the headers crossing this boundary are precisely the highest-value secrets in the system: `Authorization: Bearer sk-...`, `X-Api-Key`, tenant API keys, session cookies, and provider credentials forwarded by instrumented SDKs.

Those log lines are written to the container's stdout and captured by the `json-file` driver with `max-size: 50m, max-file: 3` — up to 150 MB of retained cleartext credentials per gateway container, on the host filesystem, readable by any process in the `docker` group.

Critically, this sink sits **entirely outside** the `transform/pii_redaction` pipeline. The platform's entire redaction investment operates on the OTLP span path; the gateway writes the same secrets to disk before and independently of it. The redaction controls asserted for SOC 2 CC6.1 and GDPR Art. 32 do not cover this path.

Traefik's `drop` default mode with an explicit per-header `keep` allowlist is the correct configuration; there is no operational need to retain `Authorization`.

---

#### C-07 — SQL Injection in the GDPR Erasure Utility, Executing as Superuser

| Field | Value |
|---|---|
| Severity | P0 — Critical |
| CVSS 3.1 | 9.1 — `AV:L/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H` |
| CWE | CWE-89 SQL Injection |
| Asset | `scripts/gdpr-erasure.sh:60,74,78` |

`TARGET_ID` is taken directly from `--user-id=` or `--customer-id=` (`:38`) and interpolated into three statements with no escaping, quoting, or validation:

```bash
curl -s $AUTH_HEADER -X POST "http://localhost:31421/?database=${CH_DB}" \
  --data-binary "ALTER TABLE telemetry_spans DELETE WHERE user_id = '${TARGET_ID}' OR customer_id = '${TARGET_ID}';"

docker exec -e PGPASSWORD="$DB_PW" -i llmobs-alloydb-db psql -U "$DB_USER" -d "$DB_NAME" \
  -c "DELETE FROM user_metadata WHERE user_id = '${TARGET_ID}';"

docker exec ... -c "INSERT INTO security_audit_logs (...) VALUES (NOW(), 'system_gdpr', 'ERASE_USER_DATA', '${TARGET_ID}', '...');"
```

`psql -c` executes multiple semicolon-separated statements. `--user-id="x'; DROP SCHEMA public CASCADE; --"` executes as `admin`, which the backup dump confirms is `SUPERUSER ... CREATEROLE CREATEDB REPLICATION BYPASSRLS`. The same input also reaches the audit-log INSERT, so the attacker controls the content of the record intended to evidence the erasure.

Three compounding defects in the same script:

- **Silent failure:** every statement ends `>/dev/null 2>&1 || true`. A failed erasure, a missing table, an authentication error, and a syntax error are all indistinguishable from success, yet line 80 unconditionally prints `GDPR data erasure completed successfully`. Under GDPR Art. 17 this produces documentary evidence of a data-subject request being honoured when no rows may have been deleted.
- **Wrong table names:** the script targets `telemetry_spans` and `user_metadata`; no migration in this package creates either. Combined with `|| true`, erasure is likely a complete no-op today.
- **Missing audit table:** `security_audit_logs` is never created, because `config/alloydb/security-audit.sql` is not mounted (H-01). The audit INSERT cannot succeed.

The script is also `-rw-r--r--` (not executable), indicating it is not exercised by the test suite.

---

#### C-08 — All Data Stores Published on `0.0.0.0` With Known Credentials

| Field | Value |
|---|---|
| Severity | P0 — Critical |
| CVSS 3.1 | 9.4 — `AV:A/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| CWE | CWE-668 Exposure of Resource to Wrong Sphere |
| Asset | `docker-compose.yml` port mappings (see Section 3) |

Fourteen of fifteen published ports omit a host-interface prefix. Docker's default publishing behaviour binds `0.0.0.0`, and Docker's iptables rules are inserted ahead of the `INPUT` chain, so a host firewall configured with UFW or firewalld **does not** filter published container ports unless explicitly integrated. `system-prereqs.sh:88` compounds this by running `sudo ufw allow in on llmobs-network to any`.

Only `llmobs-temporal`'s UI uses the correct pattern (`127.0.0.1:${PORT_TEMPORAL_UI:-31425}:8080`), demonstrating that the team knows the mechanism.

With C-01 and C-03, an adversary on the same network segment — a coffee-shop LAN, a shared office VLAN, a compromised colleague's laptop — reaches PostgreSQL as superuser, ClickHouse with access management, Redis with `+@all`, Kafka with no authentication at all, and the Temporal control plane, using credentials read from the public repository. No exploitation is required; these are supported client connections.

---

#### C-09 — Redis Arbitrary-Write / Code-Execution Path via Unscoped `default` ACL

| Field | Value |
|---|---|
| Severity | P0 — Critical |
| CVSS 3.1 | 9.1 — `AV:A/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H` |
| CWE | CWE-269 Improper Privilege Management |
| Asset | `config/redis/redis.conf:12-19` |

```
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command DEBUG ""

user default on >llmobs_redis_s3cret_2024 ~* +@all
user admin_user on >llmobs_redis_ledger_pass_2026 ~* +@all
user cost_worker on >worker_pass ~org:*:spend_micro_usd +@read +@write +hincrby
user rate_limiter on >limiter_pass ~rate:*:window +@read +@write +zadd +zremrangebyscore
```

AUD-0006 finding F-008 required ACL scoping to replace shared-password authentication. Scoped users were added — and then `default` was left enabled with `~* +@all`, so the scoping is decorative: every client can continue to authenticate as `default` with the published password and hold unrestricted access to all keys and all commands.

The `rename-command` directives disable three commands and leave the dangerous ones intact. `+@all` includes `CONFIG SET`, `MODULE LOAD`, `SAVE`, `BGSAVE`, `REPLICAOF`, and `SHUTDOWN`. The standard chain is:

```
CONFIG SET dir /var/lib/redis   ->   CONFIG SET dbfilename evil.so   ->   SAVE   ->   MODULE LOAD ./evil.so
```

which yields arbitrary code execution inside the Redis container. Because the container runs as root with no capability drops (H-12) and the port is published to the LAN (C-08), this is remotely reachable with a credential printed in the repository. `worker_pass` and `limiter_pass` are additionally trivial enough to guess.

`bind 0.0.0.0` (`:4`) with `protected-mode` unset completes the exposure.

---

#### C-10 — Temporal Authentication Non-Functional; Control Plane Open

| Field | Value |
|---|---|
| Severity | P0 — Critical |
| CVSS 3.1 | 9.1 — `AV:A/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| CWE | CWE-1188, CWE-306 |
| Asset | `docker-compose.yml:311`; `config/temporal/temporal.yaml` |

AUD-0006 item 1.4 (`HIGH-S4`, "Temporal Engine Authentication & mTLS Enforcement") is marked `[x] Complete`, closed by adding one environment variable:

```yaml
- TEMPORAL_AUTH_ENABLED=true    # docker-compose.yml:311
```

`TEMPORAL_AUTH_ENABLED` is not a variable that `temporalio/auto-setup:1.24.2` or the Temporal server reads. Temporal authorization is configured exclusively through the server config file's `global.authorization` block, specifying an `authorizer` and `claimMapper` (for example `default` / `default-jwt`), together with `global.tls` for transport security.

`config/temporal/temporal.yaml` — the file mounted at `/etc/temporal/config/temporal.yaml` — contains **no `authorization:` block and no `tls:` block**. It binds `frontend`, `history`, `matching`, and `worker` to `0.0.0.0` (`:12,18,24,30`), and the frontend gRPC port is published to the host at `31424` (`docker-compose.yml:303`).

Any client on the network segment can therefore call the full Temporal frontend API without credentials: enumerate namespaces, read complete workflow histories (which in this platform contain LLM prompts, completions, and cost attribution), start and terminate workflows, and signal running executions. Workflow history is stored pre-redaction and is not covered by the OTel transform pipeline.

The environment variable's presence is worse than its absence: it caused the finding to be closed, and it appears in `docker inspect` output as apparent evidence that authentication is enabled.

---

#### C-11 — World-Readable CA and Server TLS Private Keys

| Field | Value |
|---|---|
| Severity | P0 — Critical |
| CVSS 3.1 | 9.1 — `AV:L/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:N` |
| CWE | CWE-732 Incorrect Permission Assignment for Critical Resource |
| Asset | `scripts/generate-certs.sh:153`; `config/certs/` on disk |

```bash
openssl genrsa -out "$CA_KEY" 4096
chmod 600 "$CA_KEY"        # :138  — correct
...
openssl genrsa -out "$SERVER_KEY" 4096
chmod 644 "$SERVER_KEY"    # :153  — world-readable private key
```

Observed filesystem state is worse than the script implies:

```
-rw-r--r--  1 ... 3272 ca-key.pem       # 0644 — Root CA private key
-rw-r--r--  1 ... 3272 server-key.pem   # 0644 — gateway private key
```

Both keys are world-readable. The CA key being `0644` despite the `chmod 600` at line 138 indicates the on-disk material was produced by a path that does not apply the restriction, or was subsequently relaxed — either way the protective intent is not achieved in practice.

**Impact of the server key:** any local account can decrypt captured gateway traffic (RSA key exchange) or impersonate the gateway.

**Impact of the CA key is categorically worse.** `setup.sh` instructs operators to trust this CA for the `llmobs.*` domains. Possession of the CA private key permits minting a valid certificate for **any** name in the SAN set — and, since it is a CA, for any name at all — accepted by every client that has trusted it. Combined with `insecureSkipVerify` elsewhere (H-10) there is no compensating control.

The key material is correctly excluded from git by `.gitignore`, so the exposure is local-filesystem scope. On a shared developer host or CI runner, that is sufficient.

---

#### C-12 — Unauthenticated OTLP Ingest With Wildcard CORS

| Field | Value |
|---|---|
| Severity | P0 — Critical |
| CVSS 3.1 | 9.1 — `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:H/A:H` |
| CWE | CWE-306, CWE-942 Permissive Cross-domain Policy |
| Asset | `config/otel-collector/otel-collector-config.yaml:1-22` |

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
        cors:
          allowed_origins:
            - "http://localhost:31400"
            - "http://localhost:3000"
            - "http://127.0.0.1:31400"
            - "http://127.0.0.1:3000"
            - "*"
          allowed_headers:
            - "*"
```

Two distinct defects:

1. **No authentication.** The collector declares no `extensions:` block — no `bearertokenauth`, `basicauth`, `oidc`, or `headers_setter` — and no `auth:` on either receiver protocol. Both are published to the host (`31417`, `31418`). Anyone who can reach the port can write telemetry.
2. **Wildcard CORS defeats the allowlist.** The four specific origins are rendered meaningless by the trailing `"*"`, and `allowed_headers: ["*"]` permits arbitrary headers. Any web page in any user's browser can `POST` to the ingest endpoint.

**Impact:** unauthenticated write access to the observability data plane. An adversary can inject fabricated spans to poison the cost ledger and spend attribution, forge or bury evidence in trace history used for incident investigation, and flood the pipeline. `memory_limiter` (`limit_mib: 512`) will begin refusing data under that load, dropping legitimate telemetry — a denial of observability during precisely the window an attacker would want it. Storage growth in ClickHouse and Tempo is unbounded and unmetered.

The `debug` exporter remains in the production traces pipeline (`:97`), writing span content to collector stdout and thence to the `json-file` log driver.

---

### 5.4 High Findings — Detail

#### H-01 — Audit-Log Schema and Hardened Database Config Never Mounted

`config/alloydb/security-audit.sql` and `config/alloydb/postgresql.conf` exist, are tracked, and are referenced by the security documentation. The `llmobs-alloydb` service declares exactly one volume:

```yaml
volumes:
  - alloydb_data:/var/lib/postgresql/data    # docker-compose.yml:286-287
```

Neither file is mounted, and no init hook (`/docker-entrypoint-initdb.d`) references them. Consequences:

- `security_audit_logs` **does not exist** in any deployed database. Every write to it — including `gdpr-erasure.sh:78` — fails, silenced by `|| true`.
- AlloyDB runs stock defaults: no `ssl = on`, no `log_connections` / `log_disconnections`, no `password_encryption = scram-sha-256` enforcement, no `pgaudit`, no `log_statement`. The hardening asserted by `postgresql.conf` is not in effect, and that file also lacks any of those security directives.
- ADR-0006 finding F-009 (audit-log integrity) cannot be remediated on a table that is never created.

This is a documentation-versus-deployment gap that produces compliance evidence for a control with no runtime existence.

#### H-02 — Healthchecks Structurally Incapable of Failing

```yaml
redis:     "... ping | grep PONG || redis-cli -a ... ping | grep PONG || exit 0"   # :80
kafka:     "nc -z 127.0.0.1 9092 || exit 0"                                        # :124
alloydb:   "pg_isready ... || pg_isready ... || exit 0"                            # :291
temporal:  "nc -z 127.0.0.1 7233 || exit 0"                                        # :332
```

Every branch terminates in `exit 0`. Docker interprets exit code 0 as healthy, so four of the nine services report `healthy` unconditionally — including when the process is dead, the port is closed, or authentication is failing.

`stack-orchestration.sh:55` compounds this:

```bash
docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
  '$container' | grep -q 'healthy\|running'
```

`grep -q 'healthy\|running'` also matches `running`, and — because the pattern is unanchored — matches the substring in `unhealthy`. Both the container-level and orchestration-level readiness gates are inoperative.

**Security relevance:** the platform loses its ability to detect a service that has been stopped, crashed, or replaced. Redis failing authentication after a credential change, Temporal refusing connections, and a Kafka broker killed by an attacker are all reported as healthy, and `npm run health` proceeds to report success.

#### H-03 — Filename-Based Discovery Executes Arbitrary Repository Scripts

`manage.sh` locates each pipeline stage by filename and executes the result:

```bash
prereq_script=$(find_required_script "system-prereqs.sh" "$scripts_root")
bash "$prereq_script"                                    # manage.sh:58-59
```

`find_required_script` delegates to `discover_script_file_recursive` (`dynamic-discovery.sh:141-190`), which after two direct-path attempts performs a depth-3 DFS of `$search_root` and then a **depth-4 DFS of the entire git repository root**, returning candidates ranked by `rank_candidates` (`:84-110`). The ranking awards `+50` for the executable bit, favours shallow paths, and scores content containing `main`, `bash`, `set -e`.

Any file named `system-prereqs.sh`, `generate-certs.sh`, `port-manager.sh`, `stack-orchestration.sh`, or `test-health.sh` placed anywhere within four levels of the monorepo root becomes a candidate for execution during `npm run up`. Realistic delivery paths include a feature branch, a merged pull request touching an unrelated package, a vendored third-party directory, or a developer scratch folder. Only `.`-prefixed directories, `node_modules`, and `venv` are excluded (`:56`).

The selected script runs with the developer's privileges, and `system-prereqs.sh` immediately invokes `sudo` (H-04). This is a practical local privilege-escalation and supply-chain primitive that requires no compromise of the infra package itself.

#### H-04 — Unattended `sudo` and Firewall Modification During `npm run up`

`system-prereqs.sh` is the first stage of every `up` pipeline and executes, without confirmation:

```bash
sudo apt-get update && sudo apt-get install -y "${missing[@]}"    # :19
sudo systemctl enable --now docker                                 # :29
sudo sysctl -w vm.max_map_count=262144                             # :54
sudo ufw allow in on llmobs-network to any                          # :88
```

A routine developer command performs non-interactive package installation, permanently enables a system service, mutates kernel parameters, and **adds a firewall rule**. Line 88 is reached only when UFW is active — precisely the hosts where the operator has deliberately configured filtering — and widens it. Combined with C-08, this actively removes the one control that might have limited data-store exposure.

#### H-05 — Credentials Passed as Command-Line Arguments

| Location | Construct |
|---|---|
| `gdpr-erasure.sh:56,59` | `AUTH_HEADER="-u ${CH_USER}:${CH_PW}"` then unquoted `curl -s $AUTH_HEADER` |
| `test-health.sh:375,384-387` | same unquoted `-u user:pass` pattern, four invocations |
| `test-health.sh:469-471` | `redis-cli --user admin_user -a <literal>` and `redis-cli -a <literal>`, six invocations |
| `docker-compose.yml:80` | healthcheck `redis-cli --user admin_user -a llmobs_redis_ledger_pass_2026` |

Command-line arguments are world-readable via `/proc/<pid>/cmdline` and `ps`, are captured in shell history, and — for the compose healthcheck — are permanently visible in `docker inspect` output and to every process inside the container. `redis-cli -a` additionally emits a warning to the Redis log that the password was supplied on the command line.

The unquoted `$AUTH_HEADER` expansion is also a correctness defect: a password containing whitespace splits into separate arguments and the request proceeds unauthenticated.

#### H-06 — Kafka Fully Unauthenticated and Unencrypted, With Config Drift

```yaml
- KAFKA_LISTENERS=PLAINTEXT://:9092,EXTERNAL://:31414,CONTROLLER://:9093
- KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,EXTERNAL:PLAINTEXT
```

All three listeners, including the host-published `EXTERNAL` one, use `PLAINTEXT`. No `SASL_SSL`, no `KAFKA_SASL_ENABLED_MECHANISMS`, no `KAFKA_AUTHORIZER_CLASS_NAME`, and therefore no ACLs — Kafka's default `allow.everyone.if.no.acl.found` applies. Any LAN host can list topics, consume the full telemetry stream, produce forged events, and delete topics.

`config/kafka/server.properties` is mounted read-only at `/etc/kafka/server.properties` (`:119`) but declares a **different and incompatible** listener set:

```
listeners=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
advertised.listeners=PLAINTEXT://llmobs-kafka:9092
```

There is no `EXTERNAL` listener, and the advertised hostname (`llmobs-kafka`) does not match the compose service alias used in the environment (`llmobs-kafka-broker`). Whichever source the image honours, the two disagree, so the effective broker configuration is not determinable from either file alone. `docker-compose.prod.yml` raises replication factors to 2 on a single-broker cluster — which cannot be satisfied — and adds no security settings whatsoever.

#### H-07 — ClickHouse `default` User: Network-Unrestricted With Access Management

```xml
<default>
  <networks><ip>::/0</ip></networks>                       <!-- :10-12 -->
  <password><![CDATA[llmobs_clickhouse_s3cret_2026]]></password>
  <access_management>1</access_management>                  <!-- :15 -->
</default>
```

`::/0` permits connections from any address. `access_management: 1`, reinforced by `CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: "1"` (`docker-compose.yml:151`), grants the shared account the ability to `CREATE USER`, `GRANT`, and `CREATE ROLE` — so anyone holding the published password escalates to durable database administrator and can provision their own persistent credentials.

Separately, `docker-compose.yml:156` mounts the ACL directory **without `:ro`**:

```yaml
- ./config/clickhouse/users.d:/etc/clickhouse-server/users.d      # writable
- ./config/clickhouse/config.d:/etc/clickhouse-server/config.d:ro # correct
```

A compromised ClickHouse process can rewrite its own user and ACL definitions — and, because this is a bind mount, modify the files in the developer's working tree.

#### H-08 — Destructive Default Mode in the Backup Utility

```bash
main() {
  local mode="purge"                                        # :84
  if [ "$1" = "--backup" ] || [ "$1" = "--backup-only" ]; then
    mode="backup"
  fi
```

The default is destruction. `manage.sh:180` invokes the script with **no arguments**, so the documented `backup-purge` command runs:

```bash
$bin -f "$compose_file" down -v      # :79 — deletes every named volume
```

removing `alloydb_data`, `clickhouse_data`, `tempo_data`, `kafka_data`, and `grafana_data`.

The preceding dumps are best-effort. `backup_alloydb` runs `pg_dumpall -U admin ... 2>/dev/null || true`; `backup_clickhouse` captures only `SHOW CREATE DATABASE` — a schema string, not data — after a `FREEZE` whose snapshot is never copied out of the volume that is about to be deleted. An empty or partial dump is detected (`[ -s ... ]`) but does **not** abort the purge. A ClickHouse "backup" is therefore 58 bytes of DDL, and the purge proceeds regardless.

#### H-09 — Backups Unencrypted, World-Readable, and Containing Credential Material

Observed state of `backups/`:

```
drwxrwxr-x  2 ... backups/
-rw-rw-r--  1 ... 3359 alloydb_dump_20260828_131325.sql
-rw-rw-r--  1 ...   58 clickhouse_schema_20260828_131325.sql
```

The PostgreSQL dump is world-readable and contains, in cleartext:

```sql
ALTER ROLE admin WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION
  BYPASSRLS PASSWORD 'SCRAM-SHA-256$4096:...';
```

`pg_dumpall` includes the global role definitions with password verifiers. A world-readable file therefore hands any local account the superuser SCRAM verifier for offline cracking — trivial here, since the plaintext is published in `.env.example` anyway.

No encryption at rest, no integrity hash, no retention or rotation policy, no off-host replication, and no access control. As deployed, the backup mechanism satisfies neither the disaster-recovery objective (H-08) nor the confidentiality requirement.

#### H-10 — TLS Verification Globally Disabled Between Services

| Location | Setting | Effect |
|---|---|---|
| `docker-compose.yml:34` | `--serversTransport.insecureSkipVerify=true` | Disables certificate verification for **all** Traefik backends by default |
| `dynamic.yml:145-147,164` | `insecure-transport` applied to `otel-service` | Gateway-to-collector HTTPS is unauthenticated |
| `docker-compose.yml:37` | `--tracing.otlp.grpc.insecure=true` | Traefik's own trace export is plaintext |
| `otel-collector-config.yaml:86-87` | `otlp/tempo` `tls: insecure: true` | Collector-to-Tempo hop is plaintext |

AUD-0006 `CRIT-S2` required elimination of the plaintext internal hop. The gateway-to-collector hop was upgraded to `https://` — and then had verification disabled, so it provides encryption against a passive observer but no protection against an active one: any container on `llmobs-network` can impersonate the collector and receive **pre-redaction** spans.

The collector-to-Tempo hop remains plaintext outright. Post-redaction spans still carry prompt and completion content, which the redaction patterns do not target.

#### H-11 — Redaction Pipeline Gaps and Silent Error Suppression

| Gap | Location | Consequence |
|---|---|---|
| `error_mode: ignore` | `:35` | OTTL statement failures — bad regex, wrong context, type mismatch — are discarded silently. A broken redaction rule looks identical to a working one. |
| `resource` context covers 2 of 7 patterns | `:37-40` | Only `sk-` and `AKIA`. Resource attributes commonly carry service credentials, JWTs, and PEM material. |
| `spanevent` covers 3 of 7 patterns | `:50-54` | Bearer tokens, PEM private keys, email addresses, and card numbers survive in span events — the context most likely to hold prompt and completion payloads. |
| No `logs` or `metrics` pipeline | `:92-97` | Only `traces` is defined. Log bodies and metric labels pass through unredacted if either pipeline is later added, and OTLP log ingest is currently unhandled. |
| Span names and status messages not processed | — | Both routinely contain user-supplied content in LLM instrumentation. |
| `debug` exporter in production pipeline | `:97` | Span content written to stdout and captured by the `json-file` log driver. |

Combined with C-06, the redaction pipeline covers a narrower path than the documentation asserts, and provides no signal when it fails.

#### H-12 — All Containers Run as Root With Full Capabilities

Across all nine services, `docker-compose.yml` declares none of:

- `user:` — every container runs as root (uid 0)
- `read_only: true` — every root filesystem is writable
- `cap_drop: [ALL]` — full default capability set retained (`CAP_CHOWN`, `CAP_SETUID`, `CAP_NET_RAW`, ...)
- `security_opt: ["no-new-privileges:true"]` — setuid escalation permitted
- `pids_limit`, `cpus`, or `tmpfs` — no fork-bomb or CPU-exhaustion bound

`CAP_NET_RAW` is directly relevant: it enables packet capture on `llmobs-network`, which is the precondition for the internal-sniffing attack chain that AUD-0006 identified and this audit re-confirms (H-10).

Memory limits are absent entirely for `llmobs-traefik`, `llmobs-redis`, `llmobs-grafana`, `llmobs-tempo`, and `llmobs-temporal`; the `system-prereqs.sh` 6 GB memory gate accounts only for the four services that declare limits.

---

### 5.5 Medium Findings — Summary

| ID | Finding | Evidence | Impact |
|---|---|---|---|
| M-01 | Mutable `latest` tags on Kafka, ClickHouse, Tempo, OTel Collector, Grafana; `GF_INSTALL_PLUGINS` fetches unpinned plugins from the internet at container start; `setup.sh:27` pre-pulls `traefik:v2.10` while compose runs `traefik:v3.7` | `docker-compose.yml:86,130,168,193,226,233` | Unreproducible builds; a compromised upstream tag or plugin is adopted automatically on restart; no digest pinning or SBOM anchor |
| M-02 | `manage.sh:63` runs `generate-certs.sh --force` on every `up`, regenerating the root CA and server key each start | `scripts/manage.sh:63` | Any trust an operator established is invalidated on the next start; certificate pinning is impossible; masked by H-10, which is likely why it went unnoticed |
| M-03 | `port-manager.sh:17` `kill -9`s any PID whose `/proc/<pid>/cgroup` or `cmdline` matches `docker\|containerd\|llmobs` — matching `dockerd`, `docker-proxy`, and every container of every other project; `fuser -k` fallback at `:26` is fully indiscriminate | `scripts/ports/port-manager.sh:17,26` | Local denial of service against unrelated workloads on the host; AUD-0006 F-011 remains exploitable |
| M-04 | `reconcile_network_conflict` runs `docker network rm llmobs-network` whenever the compose-project label does not match | `scripts/prereqs/system-prereqs.sh:124-135` | Tears down networking for any other stack attached to the shared network |
| M-05 | `dynamic.yml:27-34` injects constant `X-LLMObs-Network-Signature` and `X-LLMObs-HMAC-Auth: HMAC-SHA256` as both request and response headers; nothing verifies them; `test-health.sh:199` hardcodes the "secret" `llmobs-net-sig-secret-key-v1.0` | `config/traefik/dynamic.yml:27-34`; `scripts/test-health.sh:199,207` | AUD-0006 `CRIT-S1` unremediated in substance; the response header advertises a non-existent control to attackers; the health script computes an HMAC no component validates |
| M-06 | `curl -sk` (verification disabled) at eight sites, with plaintext-HTTP fallbacks at `:524` and `:615` that make the check pass when HTTPS fails | `scripts/test-health.sh:125,181,211,213,522,613,615,702` | TLS misconfiguration and certificate failures are undetectable by the platform's own verification suite; AUD-0006 F-012 open |
| M-07 | All four Grafana datasources declared `editable: true`; AlloyDB datasource uses `sslmode: disable` | `config/grafana/provisioning/datasources/datasources.yml:9,20,35,38,47` | Grafana holds superuser credentials for both databases behind `access: proxy`; any Grafana editor pivots to arbitrary SQL, and the PostgreSQL session is plaintext |
| M-08 | Traefik carries `extra_hosts: host.docker.internal:host-gateway`, and `auth-service` targets `http://host.docker.internal:3001`; `sniStrict: false` | `docker-compose.yml:52-53`; `dynamic.yml:15,169` | The internet-facing gateway becomes a routing path onto host-local services; router selection without SNI broadens reachable backends |
| M-09 | `.env` parsed with `grep ... \| cut -d= -f2`, truncating any value containing `=` | `gdpr-erasure.sh:50-52,67-69`; `test-health.sh:314,368,420` | Base64 or randomly generated secrets are silently truncated, producing wrong credentials and failures attributed to the wrong cause; a hidden constraint on the secret alphabet |
| M-10 | `docker-compose.prod.yml:16` sets `replicas: 2` for a service with static host port publishing; the override changes no security setting | `docker-compose.prod.yml` | The production override cannot start the collector, and production carries every defect above unmodified |

### 5.6 Low Findings — Summary

| ID | Finding | Evidence |
|---|---|---|
| L-01 | `security_audit_logs` has no tamper-evidence: no hash chain, no append-only constraint, no `REVOKE UPDATE, DELETE`, and `details TEXT` is unbounded and unredacted. AUD-0006 F-009 unaddressed at schema level | `config/alloydb/security-audit.sql` |
| L-02 | `max_server_memory_usage` is hardcoded to 3.5 GiB, so the production override's 8192M cgroup limit is inert — ClickHouse will not use the additional memory | `config/clickhouse/config.d/custom.xml:20` vs `docker-compose.prod.yml:27` |
| L-03 | `Server: LLMObs-Gateway/1.0` and two `X-LLMObs-*` response headers provide fingerprintable disclosure; `X-XSS-Protection` is a deprecated control; no `Content-Security-Policy` is set | `config/traefik/dynamic.yml:30-39` |
| L-04 | Pervasive `\|\| true` under `set -e`: orchestration reports success on failure (`stack-orchestration.sh:118,123,126`), and `manage.sh:75` runs the health check with `\|\| true` so the `up` pipeline cannot fail | 4 scripts |
| L-05 | A single shared certificate serves all services with `extendedKeyUsage = serverAuth, clientAuth`, 825-day validity, no per-service identity, and no CRL or OCSP — mTLS cannot be introduced meaningfully | `config/certs/openssl-san.cnf:18`; `scripts/generate-certs.sh:33` |

---

## 6. Attack Chains

### Chain 1 — Unauthenticated Network Access to Host Root

1. Adversary reaches the host on the shared network segment and requests `http://<host>:31411/api/rawdata` (**C-04**). No credentials required. The response enumerates every route, backend URL, middleware, and certificate path.
2. The response confirms the Docker provider is active over `unix:///var/run/docker.sock`, and that the socket is mounted into the gateway container (**C-05**).
3. Adversary obtains code execution in the Traefik container — via a Traefik CVE on the unpinned image surface (**M-01**), or via the file provider watching a writable path.
4. Through the Docker socket, adversary creates a privileged container binding `/` and starts it. **Host root achieved.** `:ro` on the socket prevents none of this.
5. From the host, adversary reads `config/certs/ca-key.pem` (**C-11**, mode `0644`) and mints trusted certificates for every platform domain; reads `backups/alloydb_dump_*.sql` (**H-09**) for the superuser verifier; and reads the gateway access logs (**C-06**) for every `Authorization` header that has crossed the gateway.

**Preconditions:** network reachability only. **Detection:** none — the audit table does not exist (**H-01**), and healthchecks cannot report failure (**H-02**).

### Chain 2 — Repository Read Access to Full Data Exfiltration

1. Adversary reads `.env.example`, `config/grafana/provisioning/datasources/datasources.yml`, and `config/redis/redis.conf` from the repository (**C-03**).
2. Because `manage.sh` restores `.env` from `.env.example` on every start (**C-01**) and `setup.sh` never generated anything (**C-02**), those credentials are live on every deployment.
3. Adversary connects directly to `<host>:31420` as PostgreSQL superuser, `<host>:31421` as ClickHouse `default` with access management (**H-07**), and `<host>:31413` as Redis `default` with `+@all` (**C-09**) — all published on `0.0.0.0` (**C-08**).
4. Adversary reads the full telemetry corpus: prompts, completions, customer identifiers, cost attribution.
5. Via `CONFIG SET dir` + `MODULE LOAD` on Redis (**C-09**), adversary obtains code execution inside the Redis container, which runs as root with full capabilities (**H-12**).
6. `CAP_NET_RAW` permits packet capture on `llmobs-network`, where the collector-to-Tempo hop is plaintext (**H-10**), yielding a continuous live feed.
7. Persistence: `CREATE USER` on ClickHouse (**H-07**), or rewriting the writable `users.d` mount (**H-07**).

### Chain 3 — Compliance Evidence Fabrication

1. A data subject exercises GDPR Art. 17. An operator runs `./scripts/gdpr-erasure.sh --user-id=<id>`.
2. The ClickHouse and PostgreSQL statements target `telemetry_spans` and `user_metadata` — tables no migration in this package creates. Both fail and are suppressed by `|| true` (**C-07**).
3. The audit INSERT targets `security_audit_logs`, which does not exist because `security-audit.sql` is never mounted (**H-01**). It also fails silently.
4. The script prints `GDPR data erasure completed successfully`. **No data was deleted, and no audit record was written.**
5. Independently, an adversary supplying `--user-id="x'; DELETE FROM security_audit_logs; --"` (**C-07**) executes arbitrary SQL as superuser and can destroy whatever audit history does exist, since the table has no append-only protection (**L-01**).

---

## 7. Root Cause Analysis

| Root Cause | Findings | Systemic Issue |
|---|---|---|
| **Configuration asserted but not wired** | C-10, H-01, H-06, L-02, M-10 | Files are authored and committed, then never mounted, never read by the image, or overridden by environment variables. Nothing verifies that a config file reaches the process it configures. Remediation was closed on file existence rather than runtime effect. |
| **Credential lifecycle with no owner** | C-01, C-02, C-03, H-05, M-09 | Secrets are authored in a tracked template, propagated by `cp -f` on every start, embedded in seven tracked files, and passed on command lines. No generation, no injection, no rotation, and an active mechanism that reverts rotation. |
| **Convenience defaults carried into production** | C-04, C-05, C-06, C-08, C-12, H-10, H-12 | `api.insecure`, Docker socket, header logging, `insecureSkipVerify`, wildcard CORS, root containers, and `0.0.0.0` publishing are all development conveniences that no production override removes. `docker-compose.prod.yml` adjusts only memory and replication. |
| **Failure suppression as a coding idiom** | H-02, H-11, C-07, L-04, M-06 | `\|\| exit 0`, `\|\| true`, `error_mode: ignore`, `2>/dev/null`, and plaintext fallbacks appear throughout. Broken controls are indistinguishable from working ones, which is why five AUD-0006 items were closed in error. |
| **Dynamic behaviour in the trusted path** | H-03, M-02, M-03, M-04, H-04 | Filename-based script discovery and execution, forced certificate regeneration, pattern-matched process termination, unconditional network removal, and unattended `sudo`. The deployment tooling takes destructive and privileged actions based on heuristics. |
| **Security theatre** | M-05, C-10, C-02 | Static headers named "HMAC", an environment variable named `TEMPORAL_AUTH_ENABLED`, and a secret-generation routine that generates nothing. Each closed a finding and each supplies false assurance — actively worse than an acknowledged gap. |

---

## 8. Remediation

Full technical remediation — target files, exact configuration and code patches, verification commands, and phase sequencing — is specified in the accompanying [Technical Remediation Plan](./remediation-plan-infra-deployment-config.md).

**Immediate containment actions before any further deployment:**

1. Rebind every published port to `127.0.0.1` (C-08). Single-line change per mapping; closes the LAN exposure precondition for Chains 1 and 2.
2. Remove `--api.insecure=true` and stop publishing port `8080` (C-04).
3. Remove the Docker socket mount and switch Traefik to file-provider only (C-05).
4. Set `--accesslog.fields.headers.defaultmode=drop` and purge existing gateway logs (C-06).
5. Delete `ensure_env_file()` from `manage.sh` (C-01).
6. Treat every credential in `.env.example`, `datasources.yml`, `redis.conf`, `default-user.xml`, `gdpr-erasure.sh`, and `test-health.sh` as compromised. Rotate all of them and remove them from the tracked files (C-03).
7. `chmod 600 config/certs/*-key.pem`, then regenerate the CA and reissue, treating the current CA as compromised (C-11).
8. Revoke execute permission on `scripts/gdpr-erasure.sh` until parameterised (C-07).

---

## 9. Validation / Retest

| Finding | Retest Method | Target Result |
|---|---|---|
| C-01 | `npm run up`, then `diff .env .env.example` | Files differ; `.env` retains operator values |
| C-02 | Delete `.env`, run `./scripts/setup.sh`, inspect `.env` | Every secret is uniquely generated; no `.env.example` literal survives |
| C-03 | `git grep -nE 's3cret\|_pass_\|llmobs_admin_password\|worker_pass\|limiter_pass'` | Zero matches in tracked files |
| C-04 | `curl -s http://<host>:31411/api/rawdata` | Connection refused |
| C-05 | `docker inspect llmobs-traefik-gateway --format '{{json .Mounts}}'` | No `docker.sock` entry |
| C-06 | `docker logs llmobs-traefik-gateway \| grep -ci authorization` | `0` |
| C-07 | `./scripts/gdpr-erasure.sh --user-id="x'; SELECT 1; --"` | Input rejected; no SQL executed; non-zero exit |
| C-08 | `ss -ltnp \| grep 314` | Every listener bound to `127.0.0.1` |
| C-09 | `redis-cli -h 127.0.0.1 -p 31413 -a <pw> CONFIG SET dir /tmp` | `NOPERM`; `default` user disabled |
| C-10 | `grpcurl -plaintext <host>:31424 list` | `Unauthenticated`; `authorization:` block present in config |
| C-11 | `stat -c '%a %n' config/certs/*-key.pem` | `600` for both |
| C-12 | `curl -X POST https://<host>:31417/v1/traces -d '{}'` with no token | `401`; CORS `*` removed |
| H-01 | `psql -c "\d security_audit_logs"` | Table exists; `SHOW ssl` returns `on` |
| H-02 | `docker stop llmobs-redis-ledger`, wait, `docker ps` | Status transitions to `unhealthy` |
| H-03 | Place a marker `test-health.sh` elsewhere in the repo, run `npm run health` | The package's own script runs; the marker does not |
| H-08 | `./scripts/db-backup-and-purge.sh` with no arguments | Backup only; purge requires an explicit destructive flag |
| H-09 | `stat -c '%a' backups/*.sql` | `600`; contents encrypted |
| H-12 | `docker inspect --format '{{.Config.User}} {{.HostConfig.ReadonlyRootfs}}'` per service | Non-root uid; `true` |

---

## 10. Residual Risk

| Finding | Reason Deferral May Be Accepted | Compensating Control Required | Risk Accepted By | Review Date |
|---|---|---|---|---|
| H-06 (single-broker Kafka replication) | Acceptable for single-node development | Documented data-loss window; no production use of the single-node profile | Platform Tech Lead | Q4 2026 |
| M-01 (`latest` tags) | Rapid iteration during pre-GA | Digest pinning mandatory before the first production deployment | Infrastructure Lead | Q4 2026 |
| L-05 (single shared certificate) | Per-service identity requires a PKI decision | Deferred until the mTLS design is ratified | Security Architect | Q1 2027 |

**No P0 or remaining P1 finding is eligible for risk acceptance.** C-01 through C-12 must be closed before this stack is deployed to any shared network segment, and before it processes production or customer telemetry.

---

## 11. Appendix

### A. Evidence Index

| Evidence | Source |
|---|---|
| `.env` identical to `.env.example` | `diff .env .env.example` — no output, exit 0 |
| `CHANGE_ME` absent from `.env.example` | `grep -c 'CHANGE_ME' .env.example` — `0` |
| TLS private keys world-readable | `ls -la config/certs/` — `ca-key.pem` and `server-key.pem` both `-rw-r--r--` |
| Superuser verifier in world-readable backup | `grep 'ALTER ROLE admin' backups/alloydb_dump_20260828_131325.sql` |
| Committed Grafana credentials in history | `git log --oneline -- config/grafana/provisioning/datasources/datasources.yml` — `0883c34e`, `a3c990b0` |
| `security-audit.sql` unmounted | `docker-compose.yml:286-287` — `alloydb_data` is the only volume |
| Port bindings | `docker-compose.yml` ports sections; only `:304` restricts the interface |

### B. Tools & Versions Reviewed

Traefik v3.7 · Redis 7-alpine · Apache Kafka (KRaft, `latest`) · ClickHouse Server (`latest`) · AlloyDB Omni 15 · Grafana Tempo (`latest`) · OpenTelemetry Collector Contrib (`latest`) · Grafana (`latest`) · Temporal auto-setup 1.24.2 · Docker Compose v2 · OpenSSL 3.x · Bash 5.x

### C. Standards Mapping

| Finding Group | CIS Docker | NIST SP 800-53 | OWASP ASVS 4.0 | Regulatory |
|---|---|---|---|---|
| C-01, C-02, C-03, H-05 | 4.10 | IA-5, SC-28 | V2.10, V6.4 | SOC 2 CC6.1; ISO 27001 A.5.17 |
| C-04, C-10, C-12, H-06 | 5.7 | AC-3, IA-2 | V4.1, V13.1 | SOC 2 CC6.6; ISO 27001 A.8.5 |
| C-05, H-12 | 5.31, 5.4, 5.12, 5.25 | AC-6, CM-7 | V14.1 | ISO 27001 A.8.9 |
| C-06, H-11 | — | AU-9, SI-19 | V7.1, V8.3 | GDPR Art. 32; PCI DSS 3.4 |
| C-07, H-01, L-01 | — | AU-2, AU-9, SI-10 | V5.3, V7.3 | GDPR Art. 17/30; SOC 2 CC7.2 |
| C-08, H-10, L-05 | 5.13 | SC-7, SC-8, SC-13 | V9.1, V9.2 | ISO 27001 A.8.24 |
| C-11, H-09 | — | SC-12, SC-28, CP-9 | V6.2, V1.6 | ISO 27001 A.8.24; SOC 2 A1.2 |
| H-03, H-04, M-01, M-03 | 5.29 | CM-5, SA-12, SI-7 | V10.3, V14.2 | ISO 27001 A.8.31 |

### D. Sign-off

| Role | Name | Date |
|---|---|---|
| Independent Security Reviewer | — | August 28, 2026 |
| Lead Systems Architect | — | Pending |
| Platform Tech Lead | — | Pending |
| CISO / Compliance Owner | — | Pending |
