<div align="center">

# 🔒 Multi-Tenant Auth Service & 13-Pillar Security Engine

### Traefik-Integrated · AlloyDB Omni RLS · Argon2id · Hexagonal Ports & Adapters

*A production-grade multi-tenant authentication, RBAC authorization, organization management, audit logging, 3-tier API key permissions management, user blocking/deletion, 30-day backup retention, and 13-pillar security engine — fronted by Traefik Proxy, backed by AlloyDB Omni / PostgreSQL Row Level Security (RLS) and Redis.*

![Status](https://img.shields.io/badge/status-production--ready-brightgreen)
![Architecture](https://img.shields.io/badge/architecture-Hexagonal%20Ports%20%26%20Adapters-blueviolet)
![Gateway](https://img.shields.io/badge/gateway-Traefik%20v2.10-24A1C1)
![Database](https://img.shields.io/badge/database-AlloyDB%20Omni%20%2F%20PostgreSQL-336791)
![Tracing](https://img.shields.io/badge/tracing-OpenTelemetry-425CC7)

</div>

---

## 📖 Table of Contents

1. [Executive Summary](#-executive-summary)
2. [Standardized API Response Envelope](#-standardized-api-response-envelope)
3. [Hexagonal Ports & Adapters Architecture](#-hexagonal-ports--adapters-architecture)
4. [Organization & User Lifecycle Workflow](#-organization--user-lifecycle-workflow)
5. [Master API Reference Table (cURL, Success & Failure Envelopes)](#-master-api-reference-table-curl-success--failure-envelopes)
6. [Automated Live API Curl Test Suite](#-automated-live-api-curl-test-suite)
7. [Verified Vitest Test Suite Execution Results](#-verified-vitest-test-suite-execution-results)

---

## 🧭 Executive Summary

The `@observability/auth` platform provides enterprise multi-tenant user sign-up, organization isolation, role-based access control (RBAC), user blocking, soft deletion with 30-day backup retention lifecycle, 3-tier API key management with permission table binding, and comprehensive audit logging.

---

## 📦 Standardized API Response Envelope

### Success Envelope (`HTTP 200 / 201`)
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": { ... },
  "error": null
}
```

### Failure Envelope (`HTTP 400 / 401 / 403 / 404 / 409 / 429 / 500`)
```json
{
  "status": "error",
  "message": "Error description message",
  "data": null,
  "error": {
    "code": "ERROR_CODE_NAME",
    "details": "Detailed error context"
  }
}
```

---

## 📊 Master API Reference Table (cURL, Success & Failure Envelopes)

| # | Endpoint & Method | Purpose / Scope | Copy-Pasteable cURL Command | Success Response (`HTTP 200 / 201`) | Failure Response (`HTTP 400 / 401 / 404 / 409 / 429`) |
|---|---|---|---|---|---|
| **1** | `POST /api/v1/auth/organizations` | Create standalone multi-tenant organization | `curl -s -X POST http://localhost:3001/api/v1/auth/organizations -H "Content-Type: application/json" -d '{"name": "Acme Corp"}'` | `{"status": "success", "message": "Organization created successfully", "data": {"id": "org_fiwgpci", "name": "Acme Corp", "slug": "acme-corp"}, "error": null}` | `{"status": "error", "message": "Organization name already exists: Acme Corp", "data": null, "error": {"code": "ORG_ALREADY_EXISTS", "details": "Organization name already exists: Acme Corp"}}` |
| **2** | `POST /api/v1/auth/users` | Create user in specific org with permissions | `curl -s -X POST http://localhost:3001/api/v1/auth/users -H "Content-Type: application/json" -d '{"email": "user@acme.io", "password": "StrongPassword123!", "name": "Sarah", "org_id": "org_fiwgpci", "role": "member", "permissions": ["traces:read"]}'` | `{"status": "success", "message": "User created in target organization with specific permissions", "data": {"id": "usr_7x18fjt", "email": "user@acme.io", "org_id": "org_fiwgpci", "role": "member", "blocked": false, "user_permissions": ["traces:read"]}, "error": null}` | `{"status": "error", "message": "Email address already registered: user@acme.io", "data": null, "error": {"code": "USER_ALREADY_EXISTS", "details": "Email address already registered: user@acme.io"}}` |
| **3** | `POST /api/v1/auth/sign-in` | Authenticate user & write audit log | `curl -s -X POST http://localhost:3001/api/v1/auth/sign-in -H "Content-Type: application/json" -d '{"email": "user@acme.io", "password": "StrongPassword123!"}'` | `{"status": "success", "message": "User signed in successfully", "data": {"token": "eyJzdWI...", "user": {"id": "usr_7x18fjt", "email": "user@acme.io", "org_id": "org_fiwgpci", "role": "member"}}, "error": null}` | `{"status": "error", "message": "User account is blocked. Contact administrator.", "data": null, "error": {"code": "USER_BLOCKED", "details": "User account is blocked. Contact administrator."}}` |
| **4** | `GET /api/v1/auth/session` | Validate session token & return context | `curl -s -X GET http://localhost:3001/api/v1/auth/session -H "Authorization: Bearer <TOKEN>"` | `{"status": "success", "message": "Session token verified", "data": {"sub": "usr_7x18fjt", "email": "user@acme.io", "org": {"org_id": "org_fiwgpci", "role": "member"}}, "error": null}` | `{"status": "error", "message": "Missing or invalid Authorization header", "data": null, "error": {"code": "UNAUTHORIZED", "details": "Missing or invalid Authorization header"}}` |
| **5** | `POST /api/v1/auth/sign-up` | Combined register user & organization | `curl -s -X POST http://localhost:3001/api/v1/auth/sign-up -H "Content-Type: application/json" -d '{"email": "admin@acme.io", "password": "StrongPassword123!", "name": "Admin", "organization_name": "Acme Global", "role": "admin"}'` | `{"status": "success", "message": "User and organization successfully registered", "data": {"token": "eyJzdWI...", "user": {"id": "usr_ny2z98g", "email": "admin@acme.io", "org_name": "Acme Global"}}, "error": null}` | `{"status": "error", "message": "Organization name already exists: Acme Global", "data": null, "error": {"code": "ORG_ALREADY_EXISTS", "details": "Organization name already exists: Acme Global"}}` |
| **6** | `POST /api/v1/auth/forgot-password` | Request password reset token | `curl -s -X POST http://localhost:3001/api/v1/auth/forgot-password -H "Content-Type: application/json" -d '{"email": "user@acme.io"}'` | `{"status": "success", "message": "Password reset request processed", "data": {"resetToken": "rst_uywyfulgy5p"}, "error": null}` | `{"status": "error", "message": "Validation failed: email: Invalid email", "data": null, "error": {"code": "VALIDATION_ERROR", "details": "Validation failed: email: Invalid email"}}` |
| **7** | `POST /api/v1/auth/reset-password` | Reset password using token | `curl -s -X POST http://localhost:3001/api/v1/auth/reset-password -H "Content-Type: application/json" -d '{"token": "rst_uywyfulgy5p", "new_password": "NewStrongPass123!"}'` | `{"status": "success", "message": "Password successfully reset", "data": {"success": true}, "error": null}` | `{"status": "error", "message": "Validation failed: Invalid or expired password reset token", "data": null, "error": {"code": "VALIDATION_ERROR", "details": "Invalid or expired password reset token"}}` |
| **8** | `POST /api/v1/auth/change-password` | Change password for active user | `curl -s -X POST http://localhost:3001/api/v1/auth/change-password -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{"current_password": "OldPass123!", "new_password": "NewPass123!"}'` | `{"status": "success", "message": "Password successfully changed", "data": {"success": true}, "error": null}` | `{"status": "error", "message": "Invalid email or password credentials", "data": null, "error": {"code": "INVALID_CREDENTIALS", "details": "Invalid email or password credentials"}}` |
| **9** | `POST /api/v1/auth/api-keys` | Generate 3-tier API key bound to permissions | `curl -s -X POST http://localhost:3001/api/v1/auth/api-keys -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{"name": "Telemetry Key", "org_id": "org_fiwgpci", "key_type": "general", "permissions": ["traces:read"]}'` | `{"status": "success", "message": "API key successfully created", "data": {"rawKey": "ak_gen_org_fiwgpci_secret123", "keyRecord": {"key_id": "key_whhjgin", "org_id": "org_fiwgpci"}}, "error": null}` | `{"status": "error", "message": "insert or update on table auth_api_keys violates foreign key constraint", "data": null, "error": {"code": "INTERNAL_SERVER_ERROR", "details": "Foreign key constraint violation"}}` |
| **10** | `POST /api/v1/auth/api-keys/verify` | Verify API key & permission entitlement | `curl -s -X POST http://localhost:3001/api/v1/auth/api-keys/verify -H "Content-Type: application/json" -d '{"key": "ak_gen_org_fiwgpci_secret123", "required_permission": "traces:read"}'` | `{"status": "success", "message": "API key verified", "data": {"valid": true, "authorized": true, "record": {"key_id": "key_whhjgin"}}, "error": null}` | `{"status": "error", "message": "API key has been revoked or invalid", "data": null, "error": {"code": "API_KEY_REVOKED", "details": "API key has been revoked or invalid"}}` |
| **11** | `GET /api/v1/auth/permissions` | List all system permission definitions | `curl -s -X GET http://localhost:3001/api/v1/auth/permissions` | `{"status": "success", "message": "System permissions retrieved", "data": {"permissions": ["traces:read", "traces:write", "metrics:read", "metrics:write", "logs:read", "logs:write", "alerts:read", "alerts:write", "admin:all"]}, "error": null}` | `{"status": "error", "message": "Internal server error", "data": null, "error": {"code": "INTERNAL_SERVER_ERROR", "details": "Internal server error"}}` |
| **12** | `GET /api/v1/auth/audit-logs` | Fetch sign-in audit log security history | `curl -s -X GET http://localhost:3001/api/v1/auth/audit-logs -H "Authorization: Bearer <TOKEN>"` | `{"status": "success", "message": "Audit logs retrieved", "data": [{"id": "audit_6wbu9px", "user_id": "usr_7x18fjt", "org_id": "org_fiwgpci", "event_type": "USER_SIGNIN"}], "error": null}` | `{"status": "error", "message": "Missing or invalid Authorization header", "data": null, "error": {"code": "UNAUTHORIZED", "details": "Missing or invalid Authorization header"}}` |
| **13** | `POST /api/v1/auth/users/:id/block` | Block user login access | `curl -s -X POST http://localhost:3001/api/v1/auth/users/usr_7x18fjt/block -H "Authorization: Bearer <TOKEN>"` | `{"status": "success", "message": "User blocked successfully", "data": {"success": true, "message": "User usr_7x18fjt blocked successfully."}, "error": null}` | `{"status": "error", "message": "User not found", "data": null, "error": {"code": "USER_NOT_FOUND", "details": "User not found"}}` |
| **14** | `DELETE /api/v1/auth/users/:id` | Soft delete user with 30-day retention | `curl -s -X DELETE http://localhost:3001/api/v1/auth/users/usr_7x18fjt -H "Authorization: Bearer <TOKEN>"` | `{"status": "success", "message": "User soft-deleted with 30-day backup retention", "data": {"success": true, "message": "User usr_7x18fjt soft-deleted with 30-day backup retention."}, "error": null}` | `{"status": "error", "message": "User not found", "data": null, "error": {"code": "USER_NOT_FOUND", "details": "User not found"}}` |
| **15** | `DELETE /api/v1/auth/organizations/:id` | Soft delete organization & cascade details | `curl -s -X DELETE http://localhost:3001/api/v1/auth/organizations/org_fiwgpci -H "Authorization: Bearer <TOKEN>"` | `{"status": "success", "message": "Organization soft-deleted with 30-day backup retention", "data": {"success": true, "message": "Organization org_fiwgpci and all associated entity details soft-deleted with 30-day backup retention."}, "error": null}` | `{"status": "error", "message": "Organization not found", "data": null, "error": {"code": "ORG_NOT_FOUND", "details": "Organization not found"}}` |

---

## ⚡ Automated Live API Curl Test Suite

To run all `curl` endpoints against your local server automatically:

```bash
npm run test:curl
```

---

## 🧪 Verified Vitest Test Suite Execution Results

All **27 test cases** passed across **9 test suites**:

| Test Suite File | Scope | Total Tests | Status |
|---|---|---|---|
| [`./tests/unit/hexagonal-ports-adapters.test.ts`](./tests/unit/hexagonal-ports-adapters.test.ts) | Hexagonal Ports & Adapters Architecture | 4 | `PASSED` |
| [`./tests/unit/security-mechanisms.test.ts`](./tests/unit/security-mechanisms.test.ts) | 13 Security Pillars Unit Tests | 13 | `PASSED` |
| [`./tests/unit/auth-service.test.ts`](./tests/unit/auth-service.test.ts) | Auth Service Domain Business Logic | 2 | `PASSED` |
| [`./tests/unit/row-level-security.test.ts`](./tests/unit/row-level-security.test.ts) | AlloyDB Omni RLS & Tenant Isolation | 2 | `PASSED` |
| [`./tests/unit/real-postgres-adapter.test.ts`](./tests/unit/real-postgres-adapter.test.ts) | Real PostgreSQL Pool & Adapter | 1 | `PASSED` |
| [`./tests/integration/alloydb-omni-auth.test.ts`](./tests/integration/alloydb-omni-auth.test.ts) | AlloyDB Omni Integration | 2 | `PASSED` |
| [`./tests/contract/auth-openapi.test.ts`](./tests/contract/auth-openapi.test.ts) | OpenAPI v1 Schema & Contract Compliance | 1 | `PASSED` |
| [`./tests/e2e/auth-flow.test.ts`](./tests/e2e/auth-flow.test.ts) | End-to-End API Router Pipeline | 1 | `PASSED` |
| [`./src/features/auth/tests/unit/auth.service.test.ts`](./src/features/auth/tests/unit/auth.service.test.ts) | Feature Module Unit Test | 1 | `PASSED` |
