# Technical Remediation Plan: Critical Security Audit of llm-obs-infra Deployment Configuration

| Field | Value |
|---|---|
| Target Audit | [independent-audit-infra-deployment-config.md](./independent-audit-infra-deployment-config.md) |
| Audit ID | AUD-0007 |
| Package | `packages/configs/llm-obs-infra` |
| Scope | 39 Audit Findings (12 Critical, 12 High, 10 Medium, 5 Low) |
| Status | Open — Not Started |
| Deployment Gate | **The stack MUST NOT be deployed to any shared network segment until Phase 0 and Phase 1 are complete.** |

---

## Executive Summary & Progress Tracking

This document converts the 39 findings of AUD-0007 into an actionable, phased implementation plan. Each item names the target file, the root cause, the exact patch, and a deterministic verification command.

Unlike AUD-0006, closure of an item here requires the **verification command to pass**, not the presence of a configuration file or environment variable. Five AUD-0006 items were closed on file existence and are re-opened in Phase 1 of this plan.

### Remediation Status Overview

| Phase | Category | Items | Findings Covered | Completed | Open | Target |
|---|---|---|---|---|---|---|
| **Phase 0** | Emergency Containment (same-day, no design work) | 8 | `C-01`, `C-04`, `C-05`, `C-06`, `C-07` (partial), `C-08`, `C-11`, `H-04` (partial) | 0 | 8 | 24 hrs |
| **Phase 1** | Critical — remaining Credentials, Auth & Data Exposure | 6 | `C-02`, `C-03`, `C-07` (full), `C-09`, `C-10`, `C-12` | 0 | 6 | Sprint 1 (72 hrs) |
| **Phase 2** | High — Control Integrity & Operational Safety | 12 | `H-01` – `H-12` | 0 | 12 | Sprint 2 (14 days) |
| **Phase 3** | Medium — Supply Chain & Tooling Hardening | 10 | `M-01` – `M-10` | 0 | 10 | Sprint 3 (30 days) |
| **Phase 4** | Low — Defence in Depth | 5 | `L-01` – `L-05` | 0 | 5 | Sprint 4 (90 days) |
| **Total** | | **41 items** | **39 findings** | **0** | **41** | |

Phase 0 and Phase 1 together cover all 12 Critical findings. Item count (41) exceeds finding count (39) because `C-07` and `H-04` are addressed in two stages: containment in Phase 0, full fix in Phase 1 / Phase 2.

### Credential Rotation Register

Every value below is published in git history and must be treated as permanently disclosed. Rotation is required **in addition to** removing it from the tracked file.

| Secret | Exposed In | Action |
|---|---|---|
| `llmobs_s3cret_2026` (AlloyDB `admin`) | `.env.example`, `datasources.yml:41`, `gdpr-erasure.sh:63`, `test-health.sh:420` | Rotate + revoke SUPERUSER |
| `llmobs_redis_s3cret_2024` | `.env.example`, `redis.conf:16`, `datasources.yml:50`, `compose:69,80`, `test-health.sh:469-471` | Rotate + disable `default` user |
| `llmobs_redis_ledger_pass_2026` | `redis.conf:17`, `compose:80`, `test-health.sh:469-471` | Rotate |
| `worker_pass`, `limiter_pass` | `redis.conf:18-19` | Rotate |
| `llmobs_clickhouse_s3cret_2026` | `.env.example`, `default-user.xml:13`, `datasources.yml:27`, `compose:150` | Rotate + revoke access management |
| `llmobs_admin_password` (Grafana) | `.env.example` | Rotate |
| `llmobs-net-sig-secret-key-v1.0` | `test-health.sh:199` | Retire (see 3.5) |
| Root CA + server key | `config/certs/` at mode `0644` | Regenerate; treat old CA as compromised |
| `admin` / `password` compose fallbacks | `compose:235,279,282,309` | Delete the fallbacks entirely |

---

## Phase 0: Emergency Containment

Eight changes, no design decisions required. These close the preconditions for all three attack chains and can land in a single commit.

### Item 0.1: [Critical] Bind Every Published Port to Loopback
- **Finding ID**: `C-08`
- **Target File**: `docker-compose.yml`
- **Problem**: 14 of 15 port mappings omit a host interface, so Docker binds `0.0.0.0` and inserts iptables rules ahead of `INPUT` — UFW does not filter them. PostgreSQL, Redis, ClickHouse, Kafka and the Temporal control plane answer to the whole LAN.
- **Remediation Action**: Prefix every mapping with `127.0.0.1:`, matching the pattern already used correctly at `:304`.
- **Patch**:
  ```yaml
  # docker-compose.yml — apply to ALL ports blocks
  ports:
    - "127.0.0.1:${PORT_TRAEFIK_HTTP:-31410}:80"
    - "127.0.0.1:${PORT_TRAEFIK_HTTPS:-31419}:443"
    - "127.0.0.1:${PORT_REDIS:-31413}:6379"
    - "127.0.0.1:${PORT_KAFKA:-31414}:9092"
    - "127.0.0.1:${PORT_GRAFANA:-31415}:3000"
    - "127.0.0.1:${PORT_TEMPO:-31416}:3200"
    - "127.0.0.1:${PORT_OTEL_HTTP:-31417}:4318"
    - "127.0.0.1:${PORT_OTEL_GRPC:-31418}:4317"
    - "127.0.0.1:${PORT_ALLOYDB:-31420}:5432"
    - "127.0.0.1:${PORT_CLICKHOUSE_HTTP:-31421}:8123"
    - "127.0.0.1:${PORT_CLICKHOUSE_NATIVE:-31422}:9000"
    - "127.0.0.1:${PORT_TEMPO_OTLP_GRPC:-31423}:4317"
    - "127.0.0.1:${PORT_TEMPORAL_GRPC:-31424}:7233"
  ```
  Datastore ports (Redis, Kafka, AlloyDB, ClickHouse native, Temporal gRPC) should ideally be removed entirely — inter-service traffic uses `llmobs-network` DNS and needs no host publishing.
- **Verification**: `ss -ltnp | grep -E '314[0-9]{2}'` — every listener shows `127.0.0.1:`, none shows `0.0.0.0:` or `*:`
- **Status**: `[ ]` Open

### Item 0.2: [Critical] Disable the Unauthenticated Traefik API
- **Finding ID**: `C-04`
- **Target Files**: `docker-compose.yml:21,40`, `config/traefik/traefik.yml:6-11`
- **Problem**: `--api.insecure=true` serves the full API and dashboard on `:8080` with no authentication, published on `0.0.0.0:31411`. `GET /api/rawdata` returns every route, backend URL, middleware value and certificate path. The `dashboard-router` middlewares bind `websecure` only and protect nothing on `:8080`.
- **Remediation Action**: Remove the insecure API flag, stop publishing `:8080`, delete the `dashboard` entrypoint, and reach the dashboard only through the authenticated `websecure` router.
- **Patch**:
  ```yaml
  # docker-compose.yml — DELETE line 21 and line 40
  # - "--api.insecure=true"                          <-- remove
  # - "${PORT_TRAEFIK_DASHBOARD:-31411}:8080"        <-- remove
  command:
    - "--api.dashboard=true"      # served via the websecure router only
  ```
  ```yaml
  # config/traefik/traefik.yml
  entryPoints:
    web:
      address: ":80"
    websecure:
      address: ":443"
    # dashboard entrypoint removed

  api:
    insecure: false
    dashboard: true
  ```
  Add basic-auth to the dashboard router (pair with Item 1.4's secret handling):
  ```yaml
  # config/traefik/dynamic.yml
  http:
    middlewares:
      dashboard-auth:
        basicAuth:
          usersFile: /run/secrets/traefik_dashboard_users   # htpasswd, bcrypt
    routers:
      dashboard-router:
        middlewares: ["dashboard-auth", "security-headers", "rate-limit"]
  ```
- **Verification**: `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:31411/api/rawdata` → connection refused; `curl -sk https://llmobs.gateway:31419/api/rawdata` → `401`
- **Status**: `[ ]` Open

### Item 0.3: [Critical] Remove the Docker Socket From the Gateway
- **Finding ID**: `C-05`
- **Target Files**: `docker-compose.yml:22-24,43,47`, `config/traefik/traefik.yml:13-17`
- **Problem**: `/var/run/docker.sock:/var/run/docker.sock:ro` grants the internet-facing gateway full Docker API access. `:ro` protects the socket inode, not the API — `POST /containers/create` with `Binds: ["/:/host"]` and `Privileged: true` yields host root. CIS Docker Benchmark 5.31.
- **Remediation Action**: Delete the mount and the Docker provider. Every route already exists in `dynamic.yml` (file provider), so no functionality is lost — the `traefik.enable=true` labels become redundant and should be removed for clarity.
- **Patch**:
  ```yaml
  # docker-compose.yml — llmobs-traefik
  command:
    # - "--providers.docker=true"                          <-- remove
    # - "--providers.docker.exposedbydefault=false"        <-- remove
    # - "--providers.docker.network=llmobs-network"        <-- remove
    - "--providers.file.directory=/etc/traefik/dynamic"
    - "--providers.file.watch=true"
  volumes:
    # - /var/run/docker.sock:/var/run/docker.sock:ro       <-- remove
    - ./config/traefik/dynamic.yml:/etc/traefik/dynamic/dynamic.yml:ro
    - ./config/certs:/etc/traefik/certs:ro
  environment:
    # - DOCKER_API_VERSION=1.40                            <-- remove
  ```
  ```yaml
  # config/traefik/traefik.yml
  providers:
    file:
      directory: "/etc/traefik/dynamic"
      watch: true
  ```
  If the Docker provider is genuinely required later, front it with a socket proxy (`tecnativa/docker-socket-proxy`) exposing only `CONTAINERS=1`, never the raw socket.
- **Verification**: `docker inspect llmobs-traefik-gateway --format '{{json .Mounts}}' | grep -c docker.sock` → `0`
- **Status**: `[ ]` Open

### Item 0.4: [Critical] Stop Logging Request Headers
- **Finding ID**: `C-06`
- **Target Files**: `docker-compose.yml:31-33`, `config/traefik/traefik.yml:27-31`
- **Problem**: `defaultmode=keep` writes every request header verbatim into JSON access logs — `Authorization: Bearer sk-...`, `X-Api-Key`, tenant keys, cookies. Retained up to 150 MB per container by the `json-file` driver. This sink is entirely outside the `transform/pii_redaction` pipeline, so the platform's redaction controls do not cover it.
- **Remediation Action**: Switch to `drop` by default with an explicit allowlist of non-sensitive headers, and purge existing logs.
- **Patch**:
  ```yaml
  # docker-compose.yml
  - "--accesslog=true"
  - "--accesslog.format=json"
  - "--accesslog.fields.headers.defaultmode=drop"
  - "--accesslog.fields.headers.names.User-Agent=keep"
  - "--accesslog.fields.headers.names.Content-Type=keep"
  - "--accesslog.fields.headers.names.X-Request-Id=keep"
  - "--accesslog.fields.headers.names.Authorization=drop"
  - "--accesslog.fields.headers.names.Cookie=drop"
  ```
  ```yaml
  # config/traefik/traefik.yml
  accessLog:
    format: json
    fields:
      defaultMode: keep
      headers:
        defaultMode: drop
        names:
          User-Agent: keep
          Content-Type: keep
          X-Request-Id: keep
  ```
  Purge existing exposure: `docker rm -f llmobs-traefik-gateway` (discards the json-file log), then confirm no archived copies exist under `/var/lib/docker/containers/`.
- **Verification**: `docker logs llmobs-traefik-gateway 2>&1 | grep -ci -E 'authorization|x-api-key|cookie'` → `0`
- **Status**: `[ ]` Open

### Item 0.5: [Critical] Delete `ensure_env_file()`
- **Finding ID**: `C-01`
- **Target File**: `scripts/manage.sh:40-46,55`
- **Problem**: `cp -f "$pkg_dir/.env.example" "$pkg_dir/.env"` runs unconditionally at the head of every `up` pipeline, destroying any rotated secret and restoring the repository-published values. Verified: `.env` is byte-identical to `.env.example`.
- **Remediation Action**: Delete the function. Replace it with a fail-closed guard that requires `.env` to exist and refuses to start on known-default values.
- **Patch**:
  ```bash
  # scripts/manage.sh — replace ensure_env_file() entirely
  require_env_file() {
    local pkg_dir=$1
    if [ ! -f "$pkg_dir/.env" ]; then
      echo -e "${RED}Error: .env not found. Run './scripts/setup.sh' to generate one.${NC}" >&2
      exit 1
    fi
    if grep -qE '^(REDIS_PASSWORD|ALLOYDB_PASSWORD|CLICKHOUSE_PASSWORD|GF_SECURITY_ADMIN_PASSWORD)=(llmobs_|admin$|password$)' "$pkg_dir/.env"; then
      echo -e "${RED}Error: .env contains known-default credentials. Rotate before starting.${NC}" >&2
      exit 1
    fi
  }
  ```
  ```bash
  # scripts/manage.sh:55 — in execute_up_pipeline
  require_env_file "$pkg_dir"     # was: ensure_env_file "$pkg_dir"
  ```
- **Verification**: `npm run up && diff .env .env.example` → files differ, operator values retained
- **Status**: `[ ]` Open

### Item 0.6: [Critical] Restrict TLS Private Key Permissions
- **Finding ID**: `C-11`
- **Target Files**: `scripts/generate-certs.sh:138,153`, `config/certs/`
- **Problem**: `chmod 644 "$SERVER_KEY"` writes a world-readable gateway private key. On-disk state is worse: `ca-key.pem` is also `0644` despite the `chmod 600` at line 138. Possession of the CA key permits minting certificates trusted by every host that followed `setup.sh`'s trust instruction.
- **Remediation Action**: `chmod 600` both keys and `700` the directory; treat the existing CA as compromised and regenerate.
- **Patch**:
  ```bash
  # scripts/generate-certs.sh
  mkdir -p "$CERT_DIR" && chmod 700 "$CERT_DIR"        # in main(), replaces line 130
  ...
  openssl genrsa -out "$CA_KEY" 4096 2>/dev/null
  chmod 600 "$CA_KEY"
  ...
  openssl genrsa -out "$SERVER_KEY" 4096 2>/dev/null
  chmod 600 "$SERVER_KEY"                              # was 644 at :153
  ...
  # at end of main(), after signing:
  chmod 644 "$CA_CERT" "$SERVER_CERT"                  # certificates are public
  chmod 600 "$CA_KEY" "$SERVER_KEY"                    # keys never are
  ```
  Immediate containment on existing hosts:
  ```bash
  chmod 700 config/certs && chmod 600 config/certs/*-key.pem
  ./scripts/generate-certs.sh --force        # old CA is compromised
  # then remove the old CA from every host trust store
  ```
  Note: the container mounts `./config/certs:...:ro`. Traefik and the collector run as root today (H-12); when Item 2.12 introduces non-root users, mount the key via a Docker secret or set group ownership accordingly rather than relaxing the mode.
- **Verification**: `stat -c '%a %n' config/certs/*-key.pem` → `600` for both; `stat -c '%a' config/certs` → `700`
- **Status**: `[ ]` Open

### Item 0.7: [Critical] Revoke Execute Permission on the GDPR Script
- **Finding ID**: `C-07`
- **Target File**: `scripts/gdpr-erasure.sh`
- **Problem**: The script is injectable (Item 1.7) and silently no-ops. Until parameterised it must not be runnable, because a "successful" run produces false GDPR Art. 17 evidence.
- **Remediation Action**: Remove the execute bit and add a hard guard at the top of the file until Item 1.7 lands.
- **Patch**:
  ```bash
  chmod a-x scripts/gdpr-erasure.sh
  ```
  ```bash
  # scripts/gdpr-erasure.sh — insert after the shebang
  echo "DISABLED: this utility is unsafe (AUD-0007 C-07) and does not verify erasure." >&2
  echo "See docs/securityDoc/audits/remediation-plan-infra-deployment-config.md item 1.7" >&2
  exit 1
  ```
- **Verification**: `./scripts/gdpr-erasure.sh --user-id=test; echo $?` → non-zero, no SQL executed
- **Status**: `[ ]` Open

### Item 0.8: [High] Remove the Automatic Firewall Rule
- **Finding ID**: `H-04` (partial — the firewall element only; full item in Phase 2)
- **Target File**: `scripts/prereqs/system-prereqs.sh:82-91`
- **Problem**: `sudo ufw allow in on llmobs-network to any` widens the firewall during a routine `npm run up`, and fires only on hosts where the operator deliberately enabled filtering.
- **Remediation Action**: Replace the mutation with a warning.
- **Patch**:
  ```bash
  verify_firewall_rules() {
    if command -v ufw >/dev/null 2>&1 && sudo -n ufw status 2>/dev/null | grep -qi "Status: active"; then
      echo -e "${YELLOW}Note: UFW is active. Published container ports bypass UFW by design"
      echo -e "      (Docker inserts rules ahead of INPUT). Ports are bound to 127.0.0.1;"
      echo -e "      no firewall change is made by this script.${NC}"
    fi
  }
  ```
- **Verification**: `sudo ufw status numbered | grep -c llmobs-network` → `0` after a full `npm run up`
- **Status**: `[ ]` Open

---

## Phase 1: Critical — Credentials, Authentication & Data Exposure

### Item 1.1: [Critical] Fix Secret Generation in `setup.sh`
- **Finding ID**: `C-02`
- **Target Files**: `scripts/setup.sh:93-111`, `.env.example`
- **Problem**: The two `sed` expressions match the literal `<CHANGE_ME>`, which appears **zero** times in `.env.example` (verified). Both substitutions match nothing, `sed` exits 0, `set -e` does not fire, and the script prints two random passwords it never wrote — then reports success. Only Redis and Grafana were ever attempted; AlloyDB and ClickHouse were not.
- **Remediation Action**: Strip all real secrets from `.env.example`, replacing them with `<CHANGE_ME>` placeholders; generate every secret; and fail hard if any placeholder survives.
- **Patch**:
  ```bash
  # .env.example — secrets become placeholders
  REDIS_PASSWORD=<CHANGE_ME>
  ALLOYDB_PASSWORD=<CHANGE_ME>
  CLICKHOUSE_PASSWORD=<CHANGE_ME>
  GF_SECURITY_ADMIN_PASSWORD=<CHANGE_ME>
  REDIS_ADMIN_PASSWORD=<CHANGE_ME>
  REDIS_COST_WORKER_PASSWORD=<CHANGE_ME>
  REDIS_RATE_LIMITER_PASSWORD=<CHANGE_ME>
  OTEL_INGEST_TOKEN=<CHANGE_ME>
  ```
  ```bash
  # scripts/setup.sh — replace lines 97-109
  cp "$PKG_DIR/.env.example" "$PKG_DIR/.env"
  chmod 600 "$PKG_DIR/.env"

  SECRET_KEYS=(
    REDIS_PASSWORD REDIS_ADMIN_PASSWORD REDIS_COST_WORKER_PASSWORD
    REDIS_RATE_LIMITER_PASSWORD ALLOYDB_PASSWORD CLICKHOUSE_PASSWORD
    GF_SECURITY_ADMIN_PASSWORD OTEL_INGEST_TOKEN
  )
  for key in "${SECRET_KEYS[@]}"; do
    # hex only: avoids '=' (see item 3.9) and shell/YAML metacharacters
    val=$(openssl rand -hex 24)
    if ! grep -q "^${key}=<CHANGE_ME>$" "$PKG_DIR/.env"; then
      echo -e "  ${RED}FAIL${NC} placeholder for ${key} not found in .env.example" >&2
      exit 1
    fi
    sed -i "s|^${key}=<CHANGE_ME>$|${key}=${val}|" "$PKG_DIR/.env"
  done

  if grep -q '<CHANGE_ME>' "$PKG_DIR/.env"; then
    echo -e "  ${RED}FAIL${NC} unreplaced placeholders remain in .env" >&2
    grep -n '<CHANGE_ME>' "$PKG_DIR/.env" >&2
    exit 1
  fi
  echo -e "  ${GREEN}OK${NC} .env created with ${#SECRET_KEYS[@]} generated secrets (mode 600)"
  echo -e "    Secrets are NOT printed. Read them from .env or your secret manager."
  ```
  Note the removal of the password echo at `:104-105` — printing generated secrets to the terminal puts them in scrollback and CI logs.
- **Verification**: `rm .env && ./scripts/setup.sh && grep -c '<CHANGE_ME>\|s3cret\|llmobs_admin_password' .env` → `0`; `stat -c %a .env` → `600`
- **Status**: `[ ]` Open

### Item 1.2: [Critical] Remove Hardcoded Credentials From Tracked Files
- **Finding ID**: `C-03`
- **Target Files**: `config/grafana/provisioning/datasources/datasources.yml`, `config/redis/redis.conf`, `config/clickhouse/users.d/default-user.xml`, `scripts/gdpr-erasure.sh`, `scripts/test-health.sh`, `docker-compose.yml`
- **Problem**: Passwords are committed in seven tracked files and are present in git history (`0883c34e`, `a3c990b0`). Compose interpolation fallbacks are worse than absent defaults: `:235` yields Grafana `admin:admin` and `:279` yields PostgreSQL `admin:password` if `.env` is missing. `secureJsonData` in the Grafana file provides no protection at rest.
- **Remediation Action**: Replace every literal with an environment reference, and use the `${VAR:?message}` form so a missing value aborts the deploy instead of silently selecting a weak default.
- **Patch**:
  ```yaml
  # config/grafana/provisioning/datasources/datasources.yml
  - name: ClickHouse
    jsonData:
      username: ${CLICKHOUSE_USER}
    secureJsonData:
      password: ${CLICKHOUSE_PASSWORD}
  - name: AlloyDB
    user: ${ALLOYDB_USER}
    jsonData:
      sslmode: require              # was: disable  (see item 3.7)
    secureJsonData:
      password: ${ALLOYDB_PASSWORD}
  - name: Redis
    secureJsonData:
      password: ${REDIS_PASSWORD}
  ```
  Grafana expands `${VAR}` in provisioning files only when the variable is present in the container environment — add the four variables to the `llmobs-grafana` `environment:` block.
  ```yaml
  # docker-compose.yml — remove EVERY weak fallback
  llmobs-redis:
    command: >
      redis-server /etc/redis/redis.conf
      --requirepass ${REDIS_PASSWORD:?REDIS_PASSWORD is required}
  llmobs-clickhouse:
    environment:
      CLICKHOUSE_PASSWORD: ${CLICKHOUSE_PASSWORD:?CLICKHOUSE_PASSWORD is required}
      CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: "0"      # see item 2.7
  llmobs-grafana:
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GF_SECURITY_ADMIN_PASSWORD:?required}
      - CLICKHOUSE_USER=${CLICKHOUSE_USER:?required}
      - CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD:?required}
      - ALLOYDB_USER=${ALLOYDB_USER:?required}
      - ALLOYDB_PASSWORD=${ALLOYDB_PASSWORD:?required}
      - REDIS_PASSWORD=${REDIS_PASSWORD:?required}
  llmobs-alloydb:
    environment:
      - POSTGRES_PASSWORD=${ALLOYDB_PASSWORD:?ALLOYDB_PASSWORD is required}
      - ALLOYDB_PASSWORD=${ALLOYDB_PASSWORD:?ALLOYDB_PASSWORD is required}
  llmobs-temporal:
    environment:
      - POSTGRES_PWD=${ALLOYDB_PASSWORD:?ALLOYDB_PASSWORD is required}
  ```
  Then rotate every value in the Credential Rotation Register above, and purge history:
  ```bash
  git log --all --oneline -S 'llmobs_clickhouse_s3cret_2026'   # scope the exposure
  # coordinate a filter-repo pass or accept the values as permanently burned
  ```
- **Verification**: `git grep -nE 's3cret|_pass_2026|worker_pass|limiter_pass|llmobs_admin_password|=password$|=admin$' -- packages/configs/llm-obs-infra` → zero matches
- **Status**: `[ ]` Open

### Item 1.3: [Critical] Disable the Redis `default` User and Constrain Dangerous Commands
- **Finding ID**: `C-09`
- **Target Files**: `config/redis/redis.conf`, `docker-compose.yml:67-69,79-83`
- **Problem**: AUD-0006 F-008 added scoped ACL users and then left `user default on >... ~* +@all`, so the scoping is decorative — any client authenticates as `default` with unrestricted access. `rename-command` blocks only `FLUSHALL`, `FLUSHDB`, `DEBUG`, leaving the actual escalation path intact: `CONFIG SET dir` + `SAVE` + `MODULE LOAD` gives arbitrary code execution in a root container (H-12) on a LAN-published port (C-08).
- **Remediation Action**: Disable `default`, remove `~* +@all` from operational users, deny the escalation command set explicitly, and drive all passwords from the environment.
- **Patch**:
  ```
  # config/redis/redis.conf
  bind 0.0.0.0
  port 6379
  protected-mode yes

  maxmemory 256mb
  maxmemory-policy allkeys-lru

  # --- ACLs: default OFF, least privilege, no @admin, no @dangerous ---
  user default off

  user admin_user on >${REDIS_ADMIN_PASSWORD} ~* \
       +@all -@dangerous -config -module -save -bgsave -replicaof -slaveof \
       -shutdown -debug -flushall -flushdb -script -eval -function

  user cost_worker on >${REDIS_COST_WORKER_PASSWORD} \
       ~org:*:spend_micro_usd +@read +@write +hincrby -@dangerous

  user rate_limiter on >${REDIS_RATE_LIMITER_PASSWORD} \
       ~rate:*:window +@read +@write +zadd +zremrangebyscore -@dangerous

  appendonly yes
  appendfilename "appendonly.aof"
  appendfsync everysec
  tcp-backlog 511
  timeout 300
  tcp-keepalive 300
  loglevel notice
  databases 16
  ```
  `redis.conf` does not expand environment variables. Render it at start instead of mounting it literally, and drop `--requirepass` (which re-enables `default`):
  ```yaml
  # docker-compose.yml — llmobs-redis
  command: >
    sh -c 'envsubst < /etc/redis/redis.conf.tpl > /tmp/redis.conf
           && exec redis-server /tmp/redis.conf'
  environment:
    - REDIS_ADMIN_PASSWORD=${REDIS_ADMIN_PASSWORD:?required}
    - REDIS_COST_WORKER_PASSWORD=${REDIS_COST_WORKER_PASSWORD:?required}
    - REDIS_RATE_LIMITER_PASSWORD=${REDIS_RATE_LIMITER_PASSWORD:?required}
  volumes:
    - ./config/redis/redis.conf:/etc/redis/redis.conf.tpl:ro
  healthcheck:
    # no credentials on the command line — see item 2.5
    test: ["CMD-SHELL", "redis-cli --no-auth-warning -u \"redis://admin_user:$$REDIS_ADMIN_PASSWORD@127.0.0.1:6379\" ping | grep -q PONG"]
    interval: 10s
    timeout: 3s
    retries: 3
    start_period: 10s
  ```
  `redis:7-alpine` does not ship `envsubst`; either add `gettext` in a thin derived image or substitute with `sed`. Prefer an ACL file (`aclfile /etc/redis/users.acl`) rendered by the same mechanism if you want `ACL LOAD` without a restart.
- **Verification**: `redis-cli -h 127.0.0.1 -p 31413 -a "$REDIS_PASSWORD" PING` → `NOAUTH`/`WRONGPASS` (default disabled); `redis-cli --user admin_user -a "$REDIS_ADMIN_PASSWORD" CONFIG SET dir /tmp` → `NOPERM`
- **Status**: `[ ]` Open

### Item 1.4: [Critical] Implement Real Temporal Authentication
- **Finding ID**: `C-10`
- **Target Files**: `config/temporal/temporal.yaml`, `docker-compose.yml:302-314`
- **Problem**: AUD-0006 item 1.4 was closed by adding `TEMPORAL_AUTH_ENABLED=true`, which **is not a variable Temporal reads**. `temporal.yaml` contains no `authorization:` and no `tls:` block, binds all four services to `0.0.0.0`, and the frontend gRPC port is published at `31424`. Any LAN client can read complete workflow histories — which in this platform hold pre-redaction prompts and completions — and start or terminate workflows. The variable is worse than nothing: it closed the finding and appears in `docker inspect` as apparent evidence of authentication.
- **Remediation Action**: Configure the real `global.authorization` block with a JWT claim mapper, add TLS, remove the fictitious variable, and stop publishing the gRPC port to the host.
- **Patch**:
  ```yaml
  # config/temporal/temporal.yaml — ADD at top level
  global:
    authorization:
      jwtKeyProvider:
        keySourceURIs:
          - ${TEMPORAL_JWKS_URI}
        refreshInterval: 1m
      permissionsClaimName: permissions
      authorizer: default
      claimMapper: default-jwt
    tls:
      internode:
        server:
          certFile: /etc/temporal/certs/server.pem
          keyFile: /etc/temporal/certs/server-key.pem
          clientCaFiles: [/etc/temporal/certs/ca.pem]
          requireClientAuth: true
        client:
          serverName: llmobs.temporal
          rootCaFiles: [/etc/temporal/certs/ca.pem]
      frontend:
        server:
          certFile: /etc/temporal/certs/server.pem
          keyFile: /etc/temporal/certs/server-key.pem
          clientCaFiles: [/etc/temporal/certs/ca.pem]
          requireClientAuth: true
        client:
          serverName: llmobs.temporal
          rootCaFiles: [/etc/temporal/certs/ca.pem]

  services:
    frontend:
      rpc:
        grpcPort: 7233
        membershipPort: 6933
        bindOnIP: "0.0.0.0"     # container-internal only once the host port is removed
    history:
      rpc: { grpcPort: 7234, membershipPort: 6934, bindOnIP: "127.0.0.1" }
    matching:
      rpc: { grpcPort: 7235, membershipPort: 6935, bindOnIP: "127.0.0.1" }
    worker:
      rpc: { grpcPort: 7239, membershipPort: 6939, bindOnIP: "127.0.0.1" }
  ```
  ```yaml
  # docker-compose.yml — llmobs-temporal
  ports:
    - "127.0.0.1:${PORT_TEMPORAL_UI:-31425}:8080"
    # gRPC 7233 no longer published — reachable on llmobs-network only
  environment:
    - DB=postgres12
    - POSTGRES_PWD=${ALLOYDB_PASSWORD:?required}
    # - TEMPORAL_AUTH_ENABLED=true      <-- DELETE: not a Temporal variable
    - TEMPORAL_JWKS_URI=${TEMPORAL_JWKS_URI:?required}
  volumes:
    - ./config/temporal/temporal.yaml:/etc/temporal/config/temporal.yaml:ro
    - ./config/certs:/etc/temporal/certs:ro
  ```
  Note: `temporalio/auto-setup` renders its own config from a template and may overwrite the mount — verify the effective config with `docker exec llmobs-temporal-engine cat /etc/temporal/config/docker.yaml` and switch to the `temporalio/server` image with an explicit `--config` path if auto-setup interferes. If no JWKS provider is available yet, the interim control is removing the host port and binding the UI to loopback, documented as a known gap rather than closed.
- **Verification**: `grpcurl -plaintext 127.0.0.1:31424 list` → connection refused (port unpublished); from inside the network, an unauthenticated call returns `PermissionDenied`; `docker exec llmobs-temporal-engine grep -c 'authorization:' /etc/temporal/config/*.yaml` → non-zero
- **Status**: `[ ]` Open

### Item 1.5: [Critical] Authenticate OTLP Ingest and Fix CORS
- **Finding ID**: `C-12`
- **Target File**: `config/otel-collector/otel-collector-config.yaml:1-22,83-97`
- **Problem**: No `extensions:` block and no `auth:` on either receiver protocol — both ports accept telemetry from anyone. `allowed_origins` ends with `"*"`, which nullifies the four specific origins above it, and `allowed_headers: ["*"]` permits arbitrary headers, so any web page in any browser can POST to the ingest endpoint. Injected spans poison cost attribution and trace evidence; volume floods trip `memory_limiter` (512 MiB) and drop legitimate telemetry. The `debug` exporter also writes span content to stdout and thence to the json-file log.
- **Remediation Action**: Add `bearertokenauth`, attach it to both protocols, remove the CORS wildcard, and drop the `debug` exporter from the production pipeline.
- **Patch**:
  ```yaml
  extensions:
    bearertokenauth/ingest:
      scheme: "Bearer"
      token: "${env:OTEL_INGEST_TOKEN}"
    health_check:
      endpoint: 0.0.0.0:13133

  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
          auth:
            authenticator: bearertokenauth/ingest
          tls:
            cert_file: /etc/otel-collector/certs/server.pem
            key_file: /etc/otel-collector/certs/server-key.pem
        http:
          endpoint: 0.0.0.0:4318
          auth:
            authenticator: bearertokenauth/ingest
          tls:
            cert_file: /etc/otel-collector/certs/server.pem
            key_file: /etc/otel-collector/certs/server-key.pem
          cors:
            allowed_origins:
              - "https://llmobs.grafana"
              - "https://grafana.llmobs.local"
            allowed_headers:
              - "Content-Type"
              - "Authorization"
              - "traceparent"
            max_age: 7200

  exporters:
    otlp/tempo:
      endpoint: "llmobs-tempo:4317"
      tls:
        insecure: false                                  # see item 2.10
        ca_file: /etc/otel-collector/certs/ca.pem
        server_name_override: llmobs.tempo

  service:
    extensions: [bearertokenauth/ingest, health_check]
    telemetry:
      logs:
        level: warn
    pipelines:
      traces:
        receivers: [otlp]
        processors: [memory_limiter, transform/pii_redaction, resource, attributes, batch]
        exporters: [otlp/tempo]                          # debug exporter removed
  ```
  Add `OTEL_INGEST_TOKEN` to the collector `environment:` block and distribute it to instrumented services. For multi-tenant ingest, prefer `oidc` over a shared bearer token.
- **Verification**: `curl -sk -o /dev/null -w '%{http_code}' -X POST https://127.0.0.1:31417/v1/traces -H 'Content-Type: application/json' -d '{}'` → `401`; same request with `-H "Authorization: Bearer $OTEL_INGEST_TOKEN"` → `200`; `grep -c '"\*"' config/otel-collector/otel-collector-config.yaml` → `0`
- **Status**: `[ ]` Open

### Item 1.6: [Critical] Parameterise the GDPR Erasure Utility
- **Finding ID**: `C-07`
- **Target File**: `scripts/gdpr-erasure.sh`
- **Problem**: `TARGET_ID` is interpolated unescaped into three statements executed as PostgreSQL SUPERUSER; `psql -c` accepts multiple semicolon-separated statements, so `--user-id="x'; DROP SCHEMA public CASCADE; --"` executes. The same input reaches the audit-log INSERT, so the attacker controls the evidence record. Three compounding defects: every statement ends `|| true` so failures are invisible while line 80 prints success; the target tables `telemetry_spans` and `user_metadata` are created by no migration in this package; and `security_audit_logs` does not exist at all (H-01). The utility most likely deletes nothing today while producing false Art. 17 evidence.
- **Remediation Action**: Validate the identifier, bind parameters instead of interpolating, remove all error suppression, verify the affected row counts, and exit non-zero on any failure.
- **Patch**:
  ```bash
  #!/usr/bin/env bash
  set -Eeuo pipefail

  # --- input validation: identifiers are UUIDs or bounded alphanumerics ---
  if ! [[ "$TARGET_ID" =~ ^[A-Za-z0-9_-]{1,64}$ ]]; then
    echo -e "${RED}Error: identifier must match ^[A-Za-z0-9_-]{1,64}$${NC}" >&2
    exit 1
  fi

  # --- credentials from env, never from argv (see item 2.5) ---
  set -a; . "$PKG_DIR/.env"; set +a          # replaces grep|cut (see item 3.9)
  : "${ALLOYDB_USER:?}" "${ALLOYDB_PASSWORD:?}" "${ALLOYDB_DB:?}"
  : "${CLICKHOUSE_USER:?}" "${CLICKHOUSE_PASSWORD:?}" "${CLICKHOUSE_DB:?}"

  # --- ClickHouse: bound parameter, credentials via env not argv ---
  ch_exec() {
    local sql=$1
    CLICKHOUSE_PASSWORD="$CLICKHOUSE_PASSWORD" \
    docker exec -i -e CLICKHOUSE_PASSWORD llmobs-clickhouse-analytics \
      clickhouse-client --user "$CLICKHOUSE_USER" --database "$CLICKHOUSE_DB" \
        --param_target_id="$TARGET_ID" --query "$sql"
  }
  ch_exec "ALTER TABLE llm_spans_raw DELETE WHERE user_id = {target_id:String} OR customer_id = {target_id:String}"

  # --- PostgreSQL: psql variable binding, single statement per call ---
  pg_exec() {
    local sql=$1
    docker exec -i -e PGPASSWORD="$ALLOYDB_PASSWORD" llmobs-alloydb-db \
      psql -v ON_ERROR_STOP=1 --single-transaction \
        -U "$ALLOYDB_USER" -d "$ALLOYDB_DB" \
        -v target_id="$TARGET_ID" -c "$sql"
  }
  deleted=$(pg_exec "DELETE FROM llm_request_metadata WHERE user_id = :'target_id'" \
            | grep -oE 'DELETE [0-9]+' | awk '{print $2}')
  echo "  AlloyDB rows deleted: ${deleted:-0}"

  pg_exec "INSERT INTO security_audit_logs (actor_id, action, resource, status, details)
           VALUES ('system_gdpr', 'ERASE_USER_DATA', :'target_id', 'SUCCESS',
                   format('GDPR erasure: %s rows removed', ${deleted:-0}))"

  echo -e "${GREEN}GDPR erasure completed and audited for ${TARGET_ID}.${NC}"
  ```
  Key changes: `set -Eeuo pipefail` with **no `|| true` anywhere**, `ON_ERROR_STOP=1`, `--single-transaction`, `:'target_id'` / `{target_id:String}` binding, real table names, row-count verification, and the audit record written inside the same transaction. Confirm the actual table names against `packages/node/auth/database/migrations/` before landing.
- **Verification**: `./scripts/gdpr-erasure.sh --user-id="x'; SELECT 1; --"` → rejected by the regex, exit 1, no SQL executed; `./scripts/gdpr-erasure.sh --user-id=nonexistent` → exits non-zero or reports `0 rows` explicitly, never "completed successfully"
- **Status**: `[ ]` Open

---

## Phase 2: High — Control Integrity & Operational Safety

### Item 2.1: [High] Mount the Audit Schema and Harden `postgresql.conf`
- **Finding ID**: `H-01`
- **Target Files**: `docker-compose.yml:286-287`, `config/alloydb/postgresql.conf`
- **Problem**: `llmobs-alloydb` declares only `alloydb_data:/var/lib/postgresql/data`. Neither `security-audit.sql` nor `postgresql.conf` is mounted and no init hook references them, so `security_audit_logs` **does not exist** in any deployed database and AlloyDB runs stock defaults — no `ssl`, no `log_connections`, no `pgaudit`. The hardening the file claims is not in effect, and the file itself contains none of those directives.
- **Patch**:
  ```yaml
  # docker-compose.yml — llmobs-alloydb
  volumes:
    - alloydb_data:/var/lib/postgresql/data
    - ./config/alloydb/postgresql.conf:/etc/postgresql/postgresql.conf:ro
    - ./config/alloydb/security-audit.sql:/docker-entrypoint-initdb.d/10-security-audit.sql:ro
    - ./config/certs:/etc/postgresql/certs:ro
  command: ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
  ```
  ```
  # config/alloydb/postgresql.conf — ADD the security section
  ssl = on
  ssl_cert_file = '/etc/postgresql/certs/server.pem'
  ssl_key_file  = '/etc/postgresql/certs/server-key.pem'
  ssl_ca_file   = '/etc/postgresql/certs/ca.pem'
  ssl_min_protocol_version = 'TLSv1.2'

  password_encryption = 'scram-sha-256'

  log_connections = on
  log_disconnections = on
  log_statement = 'ddl'
  log_min_duration_statement = 1000
  log_line_prefix = '%m [%p] %q%u@%d %a %h '
  log_checkpoints = on
  log_lock_waits = on

  shared_preload_libraries = 'pgaudit'
  pgaudit.log = 'role,ddl,write'
  pgaudit.log_catalog = off
  ```
  `/docker-entrypoint-initdb.d` runs only on an empty data directory. For existing volumes, apply the schema once by hand and record it as a migration.
- **Verification**: `docker exec llmobs-alloydb-db psql -U admin -d llm_observability -c '\d security_audit_logs'` → table listed; `... -c 'SHOW ssl'` → `on`
- **Status**: `[ ]` Open

### Item 2.2: [High] Make Healthchecks Capable of Failing
- **Finding ID**: `H-02`
- **Target Files**: `docker-compose.yml:79-83,123-127,290-295,331-335`; `scripts/orchestrator/stack-orchestration.sh:55`
- **Problem**: Four healthchecks terminate every branch in `|| exit 0`, so Docker reports `healthy` unconditionally — including when the process is dead or authentication is failing. `stack-orchestration.sh:55` compounds it: `grep -q 'healthy\|running'` also matches `running`, and, being unanchored, matches the substring inside `unhealthy`. Both readiness gates are inoperative.
- **Patch**:
  ```yaml
  llmobs-kafka:
    healthcheck:
      test: ["CMD-SHELL", "/opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server 127.0.0.1:9092 >/dev/null 2>&1"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  llmobs-alloydb:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -U \"$$POSTGRES_USER\" -d \"$$POSTGRES_DB\""]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  llmobs-temporal:
    healthcheck:
      test: ["CMD-SHELL", "temporal operator cluster health --address 127.0.0.1:7233"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 60s
  ```
  Redis is covered by Item 1.3. Then fix the orchestration gate:
  ```bash
  # scripts/orchestrator/stack-orchestration.sh:55
  local check_cmd="[ \"\$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' '$container' 2>/dev/null)\" = 'healthy' ]"
  ```
  and make `wait_for_container_health` return non-zero on timeout (it currently falls through with no `return`).
- **Verification**: `docker stop llmobs-redis-ledger; sleep 40; docker ps --format '{{.Names}} {{.Status}}' | grep redis` → `unhealthy`
- **Status**: `[ ]` Open

### Item 2.3: [High] Replace Filename-Based Script Discovery With Fixed Paths
- **Finding ID**: `H-03`
- **Target Files**: `scripts/manage.sh:27-38,56-76`; `scripts/discovery/dynamic-discovery.sh:141-190`
- **Problem**: `discover_script_file_recursive` falls back to a depth-3 DFS of `$search_root` and then a **depth-4 DFS of the entire git repository root**, ranking candidates by `rank_candidates` — which awards `+50` for the executable bit. `manage.sh` then `bash`-executes the winner. Any file named `system-prereqs.sh`, `generate-certs.sh`, `port-manager.sh`, `stack-orchestration.sh`, or `test-health.sh` placed anywhere within four levels of the monorepo root can be executed during `npm run up`, with the developer's privileges — and `system-prereqs.sh` immediately calls `sudo`. Only `.`-prefixed dirs, `node_modules`, and `venv` are excluded.
- **Patch**:
  ```bash
  # scripts/manage.sh — replace find_required_script entirely
  resolve_pkg_script() {
    local rel=$1
    local path="$PKG_SCRIPTS_DIR/$rel"
    if [ ! -f "$path" ]; then
      echo -e "${RED}Error: required script missing: $path${NC}" >&2
      exit 1
    fi
    echo "$path"
  }

  # in main(), anchored to this file's own location — not discovered
  PKG_SCRIPTS_DIR="$CURRENT_SCRIPT_DIR"

  # call sites become explicit relative paths:
  bash "$(resolve_pkg_script prereqs/system-prereqs.sh)"
  bash "$(resolve_pkg_script generate-certs.sh)"
  bash "$(resolve_pkg_script ports/port-manager.sh)" "$ports"
  bash "$(resolve_pkg_script orchestrator/stack-orchestration.sh)" "$bin" "$compose_file"
  bash "$(resolve_pkg_script test-health.sh)"
  ```
  Delete `discover_script_file_recursive`, `execute_iterative_dfs`, `rank_candidates`, and `scan_content_signature` from `dynamic-discovery.sh`; `discover_file_upward` and `discover_dir_upward_containing` may stay. Also drop `discover_git_repo_root`, which only feeds the removed search.
- **Verification**: `printf '#!/bin/bash\ntouch /tmp/PWNED\n' > ../../test-health.sh && chmod +x ../../test-health.sh && npm run health; test ! -e /tmp/PWNED && echo PASS`
- **Status**: `[ ]` Open

### Item 2.4: [High] Remove Unattended `sudo` From the Deploy Path
- **Finding ID**: `H-04`
- **Target File**: `scripts/prereqs/system-prereqs.sh:10-33,48-66,82-91`
- **Problem**: `npm run up` performs non-interactive package installation (`sudo apt-get install -y`), permanently enables a system service (`sudo systemctl enable --now docker`), mutates kernel parameters (`sudo sysctl -w`), and modifies the firewall (Item 0.8) — none of it announced or consented to.
- **Patch**: Convert every mutation to a check that reports the required command and exits non-zero, leaving the privileged action to the operator.
  ```bash
  verify_host_utilities() {
    local missing=()
    for c in fuser lsof nc; do command -v "$c" >/dev/null 2>&1 || missing+=("$c"); done
    if [ ${#missing[@]} -gt 0 ]; then
      echo -e "${RED}Missing host utilities: ${missing[*]}${NC}" >&2
      echo -e "  Run: ${BOLD}sudo apt-get install -y psmisc lsof netcat-openbsd${NC}" >&2
      return 1
    fi
    echo -e "${GREEN}Host utilities present.${NC}"
  }

  verify_docker_daemon() {
    docker info >/dev/null 2>&1 && { echo -e "${GREEN}Docker daemon active.${NC}"; return 0; }
    echo -e "${RED}Docker daemon not running.${NC} Run: ${BOLD}sudo systemctl start docker${NC}" >&2
    return 1
  }

  verify_kernel_sysctls() {
    local v; v=$(sysctl -n vm.max_map_count 2>/dev/null || echo 65530)
    if [ "$v" -lt 262144 ]; then
      echo -e "${YELLOW}vm.max_map_count is ${v}; Kafka needs 262144.${NC}" >&2
      echo -e "  Run: ${BOLD}sudo sysctl -w vm.max_map_count=262144${NC}" >&2
    fi
  }
  ```
  Add `--auto-install` as an explicit opt-in flag if the convenience is wanted, and gate every `sudo` behind it.
- **Verification**: `grep -c '^\s*sudo ' scripts/prereqs/system-prereqs.sh` → `0`
- **Status**: `[ ]` Open

### Item 2.5: [High] Stop Passing Credentials on Command Lines
- **Finding ID**: `H-05`
- **Target Files**: `scripts/gdpr-erasure.sh:55-59`, `scripts/test-health.sh:368-387,469-471`, `docker-compose.yml:80`
- **Problem**: `curl -u user:pass` and `redis-cli -a <literal>` place secrets in `/proc/<pid>/cmdline`, `ps` output, and shell history; the compose healthcheck literal is permanently visible in `docker inspect` and to every process in the container. `redis-cli -a` also logs a warning that the password came from argv. The unquoted `$AUTH_HEADER` expansion is additionally a correctness bug — a password containing whitespace splits into separate arguments and the request proceeds unauthenticated.
- **Patch**:
  ```bash
  # curl: netrc or a config file on stdin, never -u
  curl -s --config - <<<"user = \"${CH_USER}:${CH_PW}\"" -X POST "$url" --data-binary "$sql"

  # redis-cli: URI from an env var, expanded inside the container
  docker exec -i -e RPW="$REDIS_ADMIN_PASSWORD" llmobs-redis-ledger \
    sh -c 'redis-cli --no-auth-warning -u "redis://admin_user:$RPW@127.0.0.1:6379" GET "$0"' "$key"

  # clickhouse-client: CLICKHOUSE_PASSWORD env var is read natively
  docker exec -i -e CLICKHOUSE_PASSWORD llmobs-clickhouse-analytics \
    clickhouse-client --user "$CH_USER" --query "$sql"
  ```
  The compose healthcheck is fixed in Item 1.3 (`$$REDIS_ADMIN_PASSWORD` resolves inside the container, so the literal never enters the compose file). Quote every expansion.
- **Verification**: `git grep -nE '(-a|-u|--password) *["'"'"']?(llmobs|\$\{?[A-Z_]*PASSWORD)' -- packages/configs/llm-obs-infra` → zero matches; `docker inspect llmobs-redis-ledger | grep -c llmobs_redis` → `0`
- **Status**: `[ ]` Open

### Item 2.6: [High] Enable Kafka Authentication and Resolve Config Drift
- **Finding ID**: `H-06`
- **Target Files**: `docker-compose.yml:100-127`, `config/kafka/server.properties`, `docker-compose.prod.yml:5-12`
- **Problem**: All three listeners map to `PLAINTEXT`, including the host-published `EXTERNAL` one. No SASL, no `KAFKA_AUTHORIZER_CLASS_NAME`, so Kafka's default `allow.everyone.if.no.acl.found` applies — any LAN host can consume the telemetry stream, produce forged events, and delete topics. Separately, the mounted `server.properties` declares an **incompatible** listener set (no `EXTERNAL`) and advertises `llmobs-kafka`, which is not the service alias in use (`llmobs-kafka-broker`); the two sources disagree, so the effective configuration is not determinable from either file. The prod override raises replication factors to 2 on a single broker — unsatisfiable — and adds no security.
- **Patch**:
  ```yaml
  # docker-compose.yml — llmobs-kafka
  environment:
    - KAFKA_LISTENERS=SASL_PLAINTEXT://:9092,CONTROLLER://:9093
    - KAFKA_ADVERTISED_LISTENERS=SASL_PLAINTEXT://llmobs-kafka-broker:9092
    - KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,SASL_PLAINTEXT:SASL_PLAINTEXT
    - KAFKA_INTER_BROKER_LISTENER_NAME=SASL_PLAINTEXT
    - KAFKA_SASL_ENABLED_MECHANISMS=SCRAM-SHA-512
    - KAFKA_SASL_MECHANISM_INTER_BROKER_PROTOCOL=SCRAM-SHA-512
    - KAFKA_AUTHORIZER_CLASS_NAME=org.apache.kafka.metadata.authorizer.StandardAuthorizer
    - KAFKA_ALLOW_EVERYONE_IF_NO_ACL_FOUND=false
    - KAFKA_SUPER_USERS=User:llmobs_admin
  ports: []      # EXTERNAL listener removed; internal network access only
  ```
  Delete the `EXTERNAL` listener and the `31414` mapping — nothing outside `llmobs-network` needs the broker. Then delete `config/kafka/server.properties` (the environment variables are authoritative for this image) or make it the single source of truth and remove the overlapping variables; do not keep both. Correct the prod override to `KAFKA_*_REPLICATION_FACTOR=1` until a multi-broker cluster exists, or add brokers.
- **Verification**: `docker exec llmobs-kafka-broker /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list` without credentials → authentication error; `ss -ltn | grep -c 31414` → `0`
- **Status**: `[ ]` Open

### Item 2.7: [High] Constrain the ClickHouse `default` User
- **Finding ID**: `H-07`
- **Target Files**: `config/clickhouse/users.d/default-user.xml`, `docker-compose.yml:151,156`
- **Problem**: `<ip>::/0</ip>` permits connections from any address, and `access_management: 1` (reinforced by `CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: "1"`) lets the shared account `CREATE USER` and `GRANT` — escalation to durable DB administrator with a published password. The `users.d` directory is also mounted **without `:ro`**, so a compromised ClickHouse process can rewrite its own ACLs and the files in the developer's working tree.
- **Patch**:
  ```xml
  <!-- config/clickhouse/users.d/default-user.xml -->
  <clickhouse>
    <users>
      <default>
        <profile>readonly</profile>
        <networks><ip>127.0.0.1</ip></networks>
        <password_sha256_hex>REPLACE_WITH_SHA256_OF_ROTATED_SECRET</password_sha256_hex>
        <quota>default</quota>
        <access_management>0</access_management>
      </default>
      <otel_writer>
        <profile>default</profile>
        <networks><ip>172.28.0.0/16</ip></networks>
        <password_sha256_hex>REPLACE_ME</password_sha256_hex>
        <access_management>0</access_management>
        <grants><query>GRANT INSERT, SELECT ON llm_telemetry_analytics.*</query></grants>
      </otel_writer>
      <grafana_reader>
        <profile>readonly</profile>
        <networks><ip>172.28.0.0/16</ip></networks>
        <password_sha256_hex>REPLACE_ME</password_sha256_hex>
        <access_management>0</access_management>
        <grants><query>GRANT SELECT ON llm_telemetry_analytics.*</query></grants>
      </grafana_reader>
    </users>
  </clickhouse>
  ```
  ```yaml
  # docker-compose.yml
  environment:
    CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: "0"
  volumes:
    - ./config/clickhouse/config.d:/etc/clickhouse-server/config.d:ro
    - ./config/clickhouse/users.d:/etc/clickhouse-server/users.d:ro    # was writable
  ```
  Use `password_sha256_hex` rather than a plaintext `<password>` element (pairs with Item 1.2).
- **Verification**: `clickhouse-client --user default --query "CREATE USER x IDENTIFIED BY 'y'"` → `ACCESS_DENIED`; `docker inspect llmobs-clickhouse-analytics --format '{{json .Mounts}}' | grep users.d` shows `"RW":false`
- **Status**: `[ ]` Open

### Item 2.8: [High] Make the Backup Utility Non-Destructive by Default
- **Finding ID**: `H-08`
- **Target File**: `scripts/db-backup-and-purge.sh:74-117`; `scripts/manage.sh:177-181`
- **Problem**: `local mode="purge"` makes destruction the default, and `manage.sh:180` invokes the script with **no arguments** — so the documented `backup-purge` command runs `docker compose down -v`, deleting `alloydb_data`, `clickhouse_data`, `tempo_data`, `kafka_data`, and `grafana_data`. The preceding dumps are best-effort (`|| true`, stderr discarded); ClickHouse "backup" is 58 bytes of `SHOW CREATE DATABASE` DDL, and the `FREEZE` snapshot is never copied out of the volume about to be deleted. An empty dump is detected but does not abort the purge.
- **Patch**:
  ```bash
  main() {
    local mode="backup"                       # safe default
    case "${1:-}" in
      --purge) mode="purge" ;;
      --backup|--backup-only|"") mode="backup" ;;
      *) echo "Usage: $0 [--backup|--purge]" >&2; exit 1 ;;
    esac
    ...
    backup_alloydb "$backup_dir" "$ts"  || { echo "AlloyDB backup FAILED" >&2; exit 1; }
    backup_clickhouse "$backup_dir" "$ts" || { echo "ClickHouse backup FAILED" >&2; exit 1; }

    if [ "$mode" = "purge" ]; then
      echo -e "${RED}About to DELETE ALL DATA VOLUMES.${NC}"
      read -r -p "Type 'DESTROY' to confirm: " confirm
      [ "$confirm" = "DESTROY" ] || { echo "Aborted."; exit 1; }
      purge_database_volumes "$compose_file" "$bin"
    fi
  }
  ```
  Remove `|| true` from both backup functions, capture real data from ClickHouse (`BACKUP TABLE ... TO Disk(...)` or copy the `shadow/` directory produced by `FREEZE` out of the volume), and return non-zero on an empty or short dump. Rename the `manage.sh` verb to `backup` and add a separate explicit `purge`.
- **Verification**: `./scripts/db-backup-and-purge.sh; docker volume ls | grep -c alloydb_data` → `1` (volume survives); `--purge` prompts for confirmation
- **Status**: `[ ]` Open

### Item 2.9: [High] Encrypt and Restrict Backups
- **Finding ID**: `H-09`
- **Target File**: `scripts/db-backup-and-purge.sh`
- **Problem**: `backups/` is `drwxrwxr-x` with dumps at `-rw-rw-r--`. The PostgreSQL dump contains `ALTER ROLE admin WITH SUPERUSER ... PASSWORD 'SCRAM-SHA-256$4096:...'` — a world-readable file hands any local account the superuser verifier. No encryption, no integrity hash, no retention policy, no off-host copy.
- **Patch**:
  ```bash
  ensure_backup_dir() {
    mkdir -p "$1" && chmod 700 "$1"
  }

  backup_alloydb() {
    local target="$backup_dir/alloydb_dump_${ts}.sql.gz.age"
    : "${BACKUP_AGE_RECIPIENT:?BACKUP_AGE_RECIPIENT required for encrypted backups}"
    docker exec -e PGPASSWORD="$ALLOYDB_PASSWORD" -i llmobs-alloydb-db \
      pg_dumpall --no-role-passwords -U "$ALLOYDB_USER" \
      | gzip -9 \
      | age -r "$BACKUP_AGE_RECIPIENT" > "$target"
    chmod 600 "$target"
    sha256sum "$target" > "${target}.sha256"
    [ -s "$target" ] || { echo "empty backup" >&2; return 1; }
  }

  prune_backups() {
    find "$1" -name '*.age' -mtime +30 -delete
  }
  ```
  `--no-role-passwords` removes the verifiers from the dump; encryption protects the remainder. Ship the artefacts off-host and verify the `.sha256` on restore.
- **Verification**: `stat -c '%a' backups backups/*` → `700` / `600`; `grep -c 'SCRAM-SHA-256' backups/*.sql* 2>/dev/null` → `0`
- **Status**: `[ ]` Open

### Item 2.10: [High] Restore TLS Verification Between Services
- **Finding ID**: `H-10`
- **Target Files**: `docker-compose.yml:34,37`, `config/traefik/dynamic.yml:145-147,164`, `config/otel-collector/otel-collector-config.yaml:86-87`
- **Problem**: `--serversTransport.insecureSkipVerify=true` disables verification for **all** Traefik backends. AUD-0006 `CRIT-S2` upgraded the gateway-to-collector hop to `https://` and then disabled verification, so it resists a passive observer but not an active one — any container on `llmobs-network` can impersonate the collector and receive **pre-redaction** spans. The collector-to-Tempo hop remains plaintext outright.
- **Patch**:
  ```yaml
  # docker-compose.yml — DELETE line 34; replace line 37
  # - "--serversTransport.insecureSkipVerify=true"     <-- remove
  - "--serversTransport.rootCAs=/etc/traefik/certs/ca.pem"
  - "--tracing.otlp.grpc.endpoint=llmobs-otel-collector:4317"
  - "--tracing.otlp.grpc.tls.ca=/etc/traefik/certs/ca.pem"
  ```
  ```yaml
  # config/traefik/dynamic.yml
  http:
    serversTransports:
      llmobs-internal:
        rootCAs:
          - /etc/traefik/certs/ca.pem
        serverName: llmobs.otel
    services:
      otel-service:
        loadBalancer:
          servers:
            - url: "https://llmobs-otel-collector:4318"
          serversTransport: llmobs-internal
  ```
  The collector exporter is corrected in Item 1.5 (`insecure: false` with `ca_file`). The certificate SAN list already includes `llmobs.otel` and `llmobs.tempo`, but the containers are addressed by service name — add `llmobs-otel-collector` and `llmobs-tempo` to `SAN_DOMAINS` in `generate-certs.sh` or set `serverName` overrides as shown.
- **Verification**: `git grep -cE 'insecureSkipVerify|insecure: true|grpc.insecure' -- packages/configs/llm-obs-infra` → `0`; ingest still returns `200`
- **Status**: `[ ]` Open

### Item 2.11: [High] Close the Redaction Pipeline Gaps
- **Finding ID**: `H-11`
- **Target File**: `config/otel-collector/otel-collector-config.yaml:34-54,92-97`
- **Problem**: `error_mode: ignore` discards OTTL failures, so a broken redaction rule is indistinguishable from a working one. The `resource` context covers 2 of 7 patterns; `spanevent` covers 3 of 7 — Bearer tokens, PEM keys, emails, and card numbers survive in span events, the context most likely to hold prompt and completion payloads. Span names and status messages are not processed. No `logs` pipeline exists at all.
- **Patch**:
  ```yaml
  processors:
    transform/pii_redaction:
      error_mode: propagate            # fail loudly; was: ignore
      trace_statements:
        - context: resource
          statements: &redact_all
            - replace_all_patterns(attributes, "value", "sk-[a-zA-Z0-9_-]{20,}", "[REDACTED_API_KEY]")
            - replace_all_patterns(attributes, "value", "AKIA[0-9A-Z]{16}", "[REDACTED_AWS_KEY]")
            - replace_all_patterns(attributes, "value", "eyJ[A-Za-z0-9-_=]+\\.[A-Za-z0-9-_=]+\\.[A-Za-z0-9-_=]*", "[REDACTED_JWT]")
            - replace_all_patterns(attributes, "value", "-----BEGIN [A-Z ]+KEY-----", "[REDACTED_PRIVATE_KEY]")
            - replace_all_patterns(attributes, "value", "Bearer\\s+[a-zA-Z0-9._\\-]+", "Bearer [REDACTED_TOKEN]")
            - replace_all_patterns(attributes, "value", "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}", "[REDACTED_EMAIL]")
            - replace_all_patterns(attributes, "value", "\\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\\b", "[REDACTED_CARD]")
        - context: span
          statements:
            - *redact_all
            - replace_pattern(name, "sk-[a-zA-Z0-9_-]{20,}", "[REDACTED_API_KEY]")
            - replace_pattern(status.message, "sk-[a-zA-Z0-9_-]{20,}", "[REDACTED_API_KEY]")
        - context: spanevent
          statements: *redact_all      # full pattern set, was 3 of 7
      log_statements:
        - context: log
          statements:
            - *redact_all
            - replace_pattern(body.string, "sk-[a-zA-Z0-9_-]{20,}", "[REDACTED_API_KEY]")
            - replace_pattern(body.string, "Bearer\\s+[a-zA-Z0-9._\\-]+", "Bearer [REDACTED_TOKEN]")

  service:
    pipelines:
      traces:
        receivers: [otlp]
        processors: [memory_limiter, transform/pii_redaction, resource, attributes, batch]
        exporters: [otlp/tempo]
      logs:
        receivers: [otlp]
        processors: [memory_limiter, transform/pii_redaction, resource, batch]
        exporters: [otlp/tempo]
  ```
  Note that `error_mode: propagate` will surface latent regex errors on first run — that is the point. Verify with a synthetic span before deploying. YAML anchors are expanded by the collector's config loader; if the version in use rejects them, inline the statement list.
- **Verification**: post a span containing all seven secret classes in span attributes, span events, resource attributes, and the span name; query Tempo and confirm every one is redacted. Also confirm the collector logs an error when a deliberately broken pattern is introduced.
- **Status**: `[ ]` Open

### Item 2.12: [High] Apply Container Hardening
- **Finding ID**: `H-12`
- **Target File**: `docker-compose.yml` (all nine services)
- **Problem**: No `user:`, `read_only:`, `cap_drop:`, `security_opt:`, `pids_limit`, or `cpus` on any service. Every container runs as root with the full default capability set — including `CAP_NET_RAW`, which enables packet capture on `llmobs-network` and is the precondition for the internal-sniffing chain. Memory limits are absent entirely for traefik, redis, grafana, tempo, and temporal, so the `system-prereqs.sh` 6 GB gate accounts for only four of nine services.
- **Patch**:
  ```yaml
  # docker-compose.yml — add an anchor and apply to every service
  x-hardening: &hardening
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    read_only: true
    pids_limit: 512

  services:
    llmobs-traefik:
      <<: *hardening
      user: "65532:65532"
      cap_add: [NET_BIND_SERVICE]     # only if binding <1024 inside the container
      tmpfs: [/tmp]
      deploy:
        resources:
          limits: { memory: 512M, cpus: "1.0" }
          reservations: { memory: 128M }

    llmobs-redis:
      <<: *hardening
      user: "999:999"
      tmpfs: [/tmp]
      volumes:
        - redis_data:/data                # AOF needs a writable volume
      deploy:
        resources:
          limits: { memory: 512M, cpus: "1.0" }
          reservations: { memory: 320M }

    llmobs-grafana:
      <<: *hardening
      user: "472:472"
      read_only: false                    # Grafana writes its plugin dir
      tmpfs: [/tmp]
      deploy:
        resources:
          limits: { memory: 1024M, cpus: "1.0" }
          reservations: { memory: 256M }

    llmobs-tempo:
      <<: *hardening
      user: "10001:10001"
      deploy:
        resources:
          limits: { memory: 1024M, cpus: "1.0" }
          reservations: { memory: 256M }

    llmobs-temporal:
      <<: *hardening
      read_only: false
      deploy:
        resources:
          limits: { memory: 1024M, cpus: "1.0" }
          reservations: { memory: 256M }
  ```
  Roll this out one service at a time — `read_only: true` will surface every path a container writes. AlloyDB and ClickHouse need writable data directories and specific uids; verify each image's expectations before enabling. Then recompute the `verify_system_memory` floor in `system-prereqs.sh` against the new complete reservation sum.
- **Verification**: `for c in $(docker ps --format '{{.Names}}' | grep llmobs); do docker inspect -f '{{.Name}} user={{.Config.User}} ro={{.HostConfig.ReadonlyRootfs}} capdrop={{.HostConfig.CapDrop}}' $c; done` → non-root uid, `ro=true` where feasible, `capdrop=[ALL]` everywhere
- **Status**: `[ ]` Open

---

## Phase 3: Medium — Supply Chain & Tooling Hardening

| Item | Finding | Target | Action | Verification |
|---|---|---|---|---|
| 3.1 | `M-01` | `docker-compose.yml:86,130,168,193,226,233`; `setup.sh:26-33` | Pin every image to an explicit version **and** digest (`clickhouse/clickhouse-server:24.8.4.13@sha256:...`); replace `GF_INSTALL_PLUGINS` with plugins baked into a derived image or pre-seeded in the `grafana_data` volume; align `setup.sh`'s `traefik:v2.10` with the `traefik:v3.7` compose actually uses, and drive the list from a single source | `grep -c 'image:.*latest' docker-compose.yml` → `0`; every `image:` line contains `@sha256:` |
| 3.2 | `M-02` | `scripts/manage.sh:63` | Drop `--force`, so `generate-certs.sh` reuses valid certificates (its `check_existing_certs` already handles the 30-day expiry window). Regenerating the root CA on every start invalidates operator trust and makes pinning impossible | `openssl x509 -noout -serial -in config/certs/ca.pem` unchanged across two `npm run up` runs |
| 3.3 | `M-03` | `scripts/ports/port-manager.sh:10-28` | Replace pattern-matched `kill -9` with container-ownership verification: resolve the port to a container via `docker ps --filter publish=<port>`, confirm the name starts with `llmobs-`, then `docker stop` it. Never kill host PIDs; delete the `fuser -k` fallback entirely. The current pattern matches `dockerd`, `docker-proxy`, and every other project's containers | Start a non-llmobs container publishing `31413`, run `npm run free-ports`, confirm it still runs |
| 3.4 | `M-04` | `scripts/prereqs/system-prereqs.sh:124-135` | Never `docker network rm` a shared network. Report the label mismatch and exit non-zero, letting the operator decide | `grep -c 'network rm' scripts/prereqs/system-prereqs.sh` → `0` |
| 3.5 | `M-05` | `config/traefik/dynamic.yml:27-34`; `scripts/test-health.sh:199,207` | Delete both `X-LLMObs-Network-Signature` and `X-LLMObs-HMAC-Auth` from request **and** response headers — they authenticate nothing and the response copy advertises a fictitious control. Remove the hardcoded `llmobs-net-sig-secret-key-v1.0` and the HMAC computation from the health script. If origin verification is genuinely required, implement mTLS (`clientAuth` on the entrypoint) or a ForwardAuth middleware against the real auth service, and update ADR-0006 to drop the Zero-Trust claim | `grep -c 'X-LLMObs-\(Network-Signature\|HMAC\)' config/traefik/dynamic.yml` → `0` |
| 3.6 | `M-06` | `scripts/test-health.sh` (8 sites) | Replace `curl -sk` with `curl -s --cacert config/certs/ca.pem`; **delete** the plaintext-HTTP fallbacks at `:524` and `:615`, which make the check pass precisely when TLS is broken. A health suite that cannot fail on a TLS misconfiguration is why AUD-0006 F-012 stayed open | `grep -c 'curl -sk\|curl -k' scripts/test-health.sh` → `0`; break the cert deliberately and confirm the suite fails |
| 3.7 | `M-07` | `config/grafana/provisioning/datasources/datasources.yml` | Set `editable: false` on all four datasources; `sslmode: require` for AlloyDB (needs Item 2.1's `ssl = on`); point the ClickHouse and AlloyDB datasources at the least-privilege read-only users from Item 2.7 rather than superusers | `grep -c 'editable: true\|sslmode: disable' datasources.yml` → `0` |
| 3.8 | `M-08` | `docker-compose.yml:52-53`; `config/traefik/dynamic.yml:15,169` | Remove `extra_hosts: host.docker.internal:host-gateway` and move the auth service onto `llmobs-network`, addressed by service name — an internet-facing gateway should not hold a route onto host-local services. Set `sniStrict: true` | `docker inspect llmobs-traefik-gateway \| grep -c host-gateway` → `0` |
| 3.9 | `M-09` | `scripts/gdpr-erasure.sh:50-52,67-69`; `scripts/test-health.sh:314,368,420` | Replace `grep \| cut -d= -f2` with `set -a; . "$PKG_DIR/.env"; set +a`, which handles `=` inside values. The current parser silently truncates base64 secrets, producing wrong credentials and failures attributed to the wrong cause | Set a password containing `=`, run `npm run health`, confirm authentication succeeds |
| 3.10 | `M-10` | `docker-compose.prod.yml` | Remove `replicas: 2` (incompatible with static host ports) or move the collector behind Traefik with dynamic ports. Then make the prod override actually security-relevant: it must assert `api.insecure=false`, `accesslog headers drop`, no Docker socket, SASL on Kafka, and the Phase 2 hardening — today it adjusts only memory and replication | `docker compose -f docker-compose.yml -f docker-compose.prod.yml config --quiet` succeeds; `docker compose ... up -d` starts the collector |

---

## Phase 4: Low — Defence in Depth

| Item | Finding | Target | Action | Verification |
|---|---|---|---|---|
| 4.1 | `L-01` | `config/alloydb/security-audit.sql` | Add tamper-evidence: `prev_hash`/`row_hash` chain columns, a `BEFORE UPDATE OR DELETE` trigger that raises, and `REVOKE UPDATE, DELETE ON security_audit_logs FROM PUBLIC, admin`. Bound `details` and redact before insert. Closes AUD-0006 F-009 at schema level (which required Item 2.1 first, since the table did not exist) | `psql -c "UPDATE security_audit_logs SET action='x'"` → error |
| 4.2 | `L-02` | `config/clickhouse/config.d/custom.xml:20` | `max_server_memory_usage` is hardcoded to 3.5 GiB, so the prod override's 8192M cgroup limit is inert. Replace with `max_server_memory_usage_to_ram_ratio` (`0.9`) so the ceiling tracks the cgroup, and move `override.xml`'s per-query limits to the same basis | With the prod override active, `SELECT value FROM system.settings WHERE name='max_server_memory_usage'` reflects ~7.3 GiB |
| 4.3 | `L-03` | `config/traefik/dynamic.yml:30-39` | Remove `Server: LLMObs-Gateway/1.0` and the `X-LLMObs-*` response headers (fingerprinting); drop the deprecated `X-XSS-Protection`; add a real `Content-Security-Policy` for the Grafana and dashboard routers | `curl -sI https://llmobs.gateway:31419 \| grep -ci 'x-llmobs\|^server:'` → `0`; CSP present |
| 4.4 | `L-04` | `db-backup-and-purge.sh`, `gdpr-erasure.sh`, `stack-orchestration.sh:118,123,126`, `manage.sh:75` | Remove `\|\| true` from every path where failure is meaningful; adopt `set -Eeuo pipefail` with an `ERR` trap; make `wait_for_*` failures abort the pipeline; drop `\|\| true` from the health-check invocation so `npm run up` can actually fail | Stop a container mid-pipeline; `npm run up` exits non-zero |
| 4.5 | `L-05` | `config/certs/openssl-san.cnf:18`; `scripts/generate-certs.sh:33-49` | Issue per-service certificates with `serverAuth` only (a separate client cert per service for mTLS), shorten leaf validity to 90 days with automated renewal, keep the CA at 825 days, and add `llmobs-otel-collector` / `llmobs-tempo` to the SAN set (needed by Item 2.10) | `openssl x509 -in config/certs/server.pem -noout -ext extendedKeyUsage` → `TLS Web Server Authentication` only |

---

## Verification Suite

Add to `tests/integration/` and run in CI, so no item can regress silently. This is the control that AUD-0006 lacked — five of its items were closed without an executable check.

```bash
#!/usr/bin/env bash
# tests/security-posture.sh — fails the build on any Phase 0/1 regression
set -Eeuo pipefail
fail=0
chk() { if eval "$2"; then echo "PASS  $1"; else echo "FAIL  $1"; fail=1; fi; }

chk "C-01 .env not overwritten by .env.example" '! diff -q .env .env.example >/dev/null 2>&1'
chk "C-02 no placeholders or default secrets in .env" '! grep -qE "CHANGE_ME|s3cret|llmobs_admin_password" .env'
chk "C-03 no hardcoded secrets in tracked files" '! git grep -qE "s3cret|_pass_2026|worker_pass|limiter_pass|=password$" -- .'
chk "C-04 traefik dashboard not published"     '! grep -q "api.insecure=true" docker-compose.yml'
chk "C-05 docker socket not mounted"           '! grep -q "docker.sock" docker-compose.yml'
chk "C-06 request headers not logged"          'grep -q "headers.defaultmode=drop" docker-compose.yml'
chk "C-08 all ports bound to loopback"         '! grep -qE "^\s+- \"\\\$\{PORT_" docker-compose.yml'
chk "C-09 redis default user disabled"         'grep -q "user default off" config/redis/redis.conf'
chk "C-10 temporal authorization configured"   'grep -q "authorization:" config/temporal/temporal.yaml'
chk "C-11 private keys are mode 600"           '[ "$(stat -c %a config/certs/server-key.pem)" = 600 ] && [ "$(stat -c %a config/certs/ca-key.pem)" = 600 ]'
chk "C-12 no wildcard CORS"                    '! grep -qE "^\s+- \"\*\"" config/otel-collector/otel-collector-config.yaml'
chk "H-02 no self-passing healthchecks"        '! grep -q "|| exit 0" docker-compose.yml'
chk "H-03 no recursive script discovery"       '! grep -q "discover_script_file_recursive" scripts/manage.sh'
chk "H-04 no unattended sudo"                  '! grep -qE "^\s*sudo " scripts/prereqs/system-prereqs.sh'
chk "H-08 backup default is non-destructive"   'grep -q "local mode=\"backup\"" scripts/db-backup-and-purge.sh'
chk "H-10 no TLS verification bypass"          '! git grep -qE "insecureSkipVerify|insecure: true" -- .'
chk "H-11 redaction errors propagate"          'grep -q "error_mode: propagate" config/otel-collector/otel-collector-config.yaml'
chk "M-01 no mutable image tags"               '! grep -q "image:.*:latest" docker-compose.yml'
chk "M-06 no insecure curl in health suite"    '! grep -qE "curl -sk|curl -k" scripts/test-health.sh'
exit $fail
```

---

## Dependency Order

Several items must land in sequence:

| First | Then | Why |
|---|---|---|
| 1.1 (`setup.sh` generation) | 1.2 (remove hardcoded creds) | The `${VAR:?}` forms fail closed, so generation must work before the fallbacks are removed |
| 1.2 (env-driven creds) | 1.3 (Redis ACLs), 2.7 (ClickHouse users) | Both configs consume the generated secrets |
| 0.6 / 4.5 (cert handling) | 2.10 (TLS verification) | Verification requires SANs that match the addresses actually used |
| 2.1 (mount audit schema) | 1.6 (GDPR audit insert), 4.1 (tamper-evidence) | The table must exist before anything writes to or constrains it |
| 2.12 (non-root containers) | 0.6 (key modes) | `chmod 600` on a host-mounted key requires the container uid to have read access |
| 1.5 (ingest auth) | 3.10 (prod override) | The collector token must exist before the override asserts it |

---

## Sign-off

| Phase | Owner | Reviewer | Completed |
|---|---|---|---|
| Phase 0 — Emergency Containment | | | |
| Phase 1 — Critical | | | |
| Phase 2 — High | | | |
| Phase 3 — Medium | | | |
| Phase 4 — Low | | | |

**Closure criterion:** an item may be marked `[x]` only when its verification command has been executed and passes. AUD-0006 closed five items on the presence of a configuration file or environment variable that had no runtime effect; that failure mode is what this criterion exists to prevent.
