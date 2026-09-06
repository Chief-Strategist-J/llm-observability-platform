# Acceptable Use Policy (AUP) — Platform Infrastructure (`llm-obs-infra`)

| Field | Value |
|---|---|
| Policy ID | AUP-LLMOBS-INFRA-001 |
| Policy Owner | Chief Information Security Officer (CISO) |
| Approved By | Security & Infrastructure Steering Committee |
| Target Package | `packages/configs/llm-obs-infra` |
| Effective Date | 2026-08-28 |
| Review Cycle | Annual |

---

## 1. Purpose & Scope

This policy governs the acceptable operational use, deployment configuration, administrative credential management, and data access policies for the central container infrastructure package `packages/configs/llm-obs-infra`.

Applies to all platform engineers, DevOps personnel, SecOps analysts, and developers interacting with container environments, database instances, network bindings, and telemetry pipelines.

---

## 2. Policy Requirements

| Domain | Mandatory Rule | Violation Risk |
|---|---|---|
| **Container Execution** | Containers MUST execute with non-root security context (`user: 1000:1000`). | Privileged Host Escalation |
| **Docker Socket** | Traefik mounts `/var/run/docker.sock:ro` strictly read-only. Modifying to read-write is forbidden. | Arbitrary Container Spawning |
| **Credential Management** | Plaintext production passwords in `.env` files committed to Git repositories are strictly prohibited. | Credential Leakage |
| **Network Bindings** | Containers MUST operate inside private bridge network `llmobs-network`. Exposing DB raw ports to public WAN is banned. | Data Exfiltration |
| **Host Port Range** | Custom container deployments MUST restrict host bindings strictly to designated range (`31410`–`31425`). | Port Collisions |
| **Database Access** | Direct production database modification without audit logging (`pgaudit`) is forbidden. | Unaudited Data Tampering |

---

## 3. Prohibited Activities

1. **Disabling Traefik Security Headers**: Removing rate-limiting, CORS sanitization, or HSTS middlewares from `config/traefik/dynamic.yml`.
2. **Plaintext Telemetry Export**: Exposing OTLP HTTP/gRPC ports without host firewall protection or TLS encryption.
3. **Bypassing Health Checks**: Deploying stack configurations with health check scripts (`scripts/test-health.sh`) disabled.

---

## 4. Enforcement & Compliance

Violations of this policy trigger immediate SecOps alert escalation, revocation of infrastructure write permissions, and mandatory security audit remediation.
