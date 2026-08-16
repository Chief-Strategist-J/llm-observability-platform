# `@observability/auth` Service & SDK

Multi-tenant authentication, RBAC authorization, organization management, audit logging, 3-tier API key permissions management, and 13-pillar security engine for the Observability Platform.

---

## 🚀 Feature List

- **Multi-Tenant Organization Management**: Unique organization registration, slug enforcement, and tenant isolation.
- **Role-Based Access Control (RBAC)**: Enforces `admin`, `member`, and `viewer` roles with extensible permission scopes.
- **3-Tier API Key Lifecycle**:
  - `general` (`ak_gen_`): Production API keys bound to granular permission tables (`traces:read`, `metrics:read`, `logs:read`).
  - `testing` (`ak_tst_`): Sandbox/testing environment API keys.
  - `super_secret` (`ak_sec_`): Elevated system access keys with wildcard entitlement.
- **13-Pillar Security Hardening Engine**:
  1. **Password Hashing**: Salted Argon2id hashing.
  2. **Token Revocation**: Session token blacklisting and immediate session invalidation.
  3. **Brute-Force Protection**: Account lockout after 5 consecutive failed login attempts.
  4. **Rate Limiting**: Sliding window request rate limiter.
  5. **Input Validation**: Strict Zod schema validation & sanitization.
  6. **CSRF Protection**: Double-submit anti-CSRF token verification.
  7. **XSS Protection**: HTML encoding and script tag stripping.
  8. **SQL Injection Prevention**: 100% parameterized queries (`AUTH_QUERIES`).
  9. **Secrets Management**: Pluggable `SecretStorePort` / `EnvSecretStoreAdapter`.
  10. **Credential-Stuffing Protection**: Multi-account login attempt anomaly detection per IP.
  11. **Device / Session Tracking**: Active device fingerprinting and user-agent tracking.
  12. **IP / Device Anomaly Detection**: Flagging logins from unrecognized devices/locations.
  13. **Step-Up Authentication**: Multi-factor OTP generation & verification for sensitive operations.
- **Database Row Level Security (RLS)**: AlloyDB Omni / PostgreSQL RLS policies (`rls_auth_users_tenant_isolation`, `rls_auth_api_keys_tenant_isolation`, `rls_auth_audit_logs_tenant_isolation`) enforcing tenant boundaries using `app.current_org_id`.
- **Security Audit Logging**: Captures `X-Forwarded-For` IP address, `User-Agent`, timestamp, and user context on every sign-in event.
- **Traefik & Reverse Proxy Adapter Pattern**: Traefik Proxy container configuration (`traefik:v2.10`) with `ReverseProxyPort` adapter interface (`TraefikProxyAdapter`, `EnvoyProxyAdapter`).
- **Allure Gold Standard Test Suite**: Fully automated test suite with HTML Allure reporting output (`vitest.config.ts`, 19 passing test cases across 5 test suites).

---

## 🏗️ Architecture

```
                               ┌──────────────────────────────────────────┐
                               │           Traefik Proxy (80/8080)        │
                               └────────────────────┬─────────────────────┘
                                                    │ (ReverseProxyPort)
                                                    ▼
                               ┌──────────────────────────────────────────┐
                               │     AuthRestV1Router (/api/v1/auth)      │
                               └────────────────────┬─────────────────────┘
                                                    │
                               ┌────────────────────┴─────────────────────┐
                               │             AuthService Engine           │
                               │    (SecurityEngine, Zod, Argon2id, JWT)  │
                               └────────────────────┬─────────────────────┘
                                                    │
          ┌─────────────────────────────────────────┼─────────────────────────────────────────┐
          ▼                                         ▼                                         ▼
┌───────────────────┐                     ┌───────────────────┐                     ┌───────────────────┐
│  5 Data Pillars   │                     │  AlloyDB Omni RLS │                     │  Redis Store      │
│ schema/           │                     │ (ENABLE RLS ON    │                     │ (Session Cache,   │
│ queries/          │                     │  auth_users,      │                     │  Revocation,      │
│ rules/            │                     │  auth_api_keys,   │                     │  Rate Limiting)   │
│ machines/         │                     │  auth_audit_logs) │                     └───────────────────┘
│ workflows/        │                     └───────────────────┘
└───────────────────┘
```

### The 5 Feature Data Pillars (`src/features/auth/`)

1. **`schema/auth.schema.ts`**: Zod entity contracts & bidirectional ACL `fromApi` / `toApi` JSON mapping rules.
2. **`queries/auth.queries.ts`**: Flow-by-flow parameterized queries (`FLOW_SIGN_UP`, `FLOW_SIGN_IN`, `TENANT_RLS`).
3. **`rules/auth.rules.ts`**: Declarative business decision rules with priority weights and deny-override resolution.
4. **`machines/auth-session.machine.ts`**: Session state machine graph (`unauthenticated` -> `authenticating` -> `active_session`).
5. **`workflows/auth-provisioning.workflow.ts`**: Automation workflow DAG definition.

---

## 🧪 Allure Test Suite Execution

Run unit, contract, RLS, and end-to-end API tests with Allure report generation:

```bash
npm run test:allure
```

### Verified Test Suite Breakdown (19/19 Tests Passing)

- **Security Mechanisms Test Suite**: 13/13 passing
- **Row Level Security (RLS) Test Suite**: 2/2 passing
- **Auth Service Unit Test Suite**: 2/2 passing
- **End-to-End API Flow Test Suite**: 1/1 passing
- **OpenAPI v1 Contract Compliance Test Suite**: 1/1 passing

---

## 🔮 Roadmap & Next Commits

- [ ] **OAuth2 / OIDC SSO Integration**: OpenID Connect provider support (Google, GitHub, Okta).
- [ ] **WebAuthn / Passkeys**: FIDO2 biometric authentication for passwordless sign-in.
- [ ] **Envoy Proxy Mesh Integration**: Production Envoy configuration utilizing `EnvoyProxyAdapter`.
- [ ] **Distributed Redis Cluster Rate Limiting**: Distributed token bucket implementation across multi-region clusters.
