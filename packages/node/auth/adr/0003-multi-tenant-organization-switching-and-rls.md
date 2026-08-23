# ADR 0003: N-to-N Multi-Tenant Organization Context Switching & RLS

- **Status**: Accepted
- **Date**: 2026-08-23
- **Context**: Users can belong to multiple organizations. Switching organization context must issue a updated JWT token scoped to the target organization while enforcing Row Level Security (RLS) policies at the database layer.

---

## 🏛 High-Level Design (HLD)

```mermaid
flowchart TD
    subgraph Client["Client Application"]
        OrgSelector["UI Org Switcher Dropdown"]
        Saga["Redux Auth Saga"]
    end

    subgraph Service["Auth Microservice (:3001)"]
        Router["AuthRestV1Router"]
        ServiceCore["AuthService Engine"]
        TokenEngine["JWT Token Engine"]
    end

    subgraph Database["AlloyDB / PostgreSQL Storage (:31412)"]
        UserOrgs[("auth_user_organizations Mapping Table")]
        OrgTable[("auth_organizations Table")]
        RLSPolicy["PostgreSQL Row-Level Security (RLS) Policy"]
    end

    OrgSelector -->|Select Target Org| Saga
    Saga -->|POST /api/v1/auth/organizations/:id/switch| Router
    Router --> ServiceCore

    ServiceCore -->|Verify User Membership| UserOrgs
    ServiceCore -->|Fetch Target Org Details| OrgTable
    ServiceCore -->|Issue Scoped JWT Token| TokenEngine

    ServiceCore -.->|Set RLS Session Context app.current_org_id| RLSPolicy
```

---

## 🔬 Low-Level Design (LLD)

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client Application
    participant Router as AuthRestV1Router
    participant Service as AuthService Engine
    participant DB as AlloyDB / PostgreSQL
    participant Redis as Redis Denylist

    Client->>Router: POST /api/v1/auth/organizations/org_target/switch (Bearer JWT)
    Router->>Service: handleVerifySession(authHeader)
    Service->>Redis: Check if token is revoked in Redis denylist
    Redis-->>Service: Null (Active Token)

    Router->>Service: handleSwitchOrganization(userId, targetOrgId, token)
    Service->>DB: SELECT role FROM auth_user_organizations WHERE user_id = $1 AND org_id = $2
    
    alt User is NOT a member of target org
        DB-->>Service: Null (No membership row)
        Service-->>Router: Throw AuthError ("User does not belong to target organization")
        Router-->>Client: HTTP 403 Forbidden
    else Membership Verified
        DB-->>Service: Member role (e.g. "admin" or "owner")
        Service->>DB: SELECT * FROM auth_organizations WHERE org_id = $2 AND deleted_at IS NULL
        DB-->>Service: Organization details

        Service->>Service: Generate new JWT Token with payload { sub: userId, org: { org_id: targetOrgId, role: memberRole } }
        Service-->>Router: Return { status: "success", token: newJwt, payload: { ... } }
        Router-->>Client: HTTP 200 OK Response Payload
    end
```

---

## 📋 Multi-Tenant Isolation Principles

1. **N-to-N Mapping**: User and Organization relationships are decoupled via `auth_user_organizations` table.
2. **Context Switching**: Switching active organization generates a fresh, signed JWT token with updated scope without forcing full re-authentication.
3. **Database RLS**: Database queries set `SET LOCAL app.current_org_id = 'org_xxx'` to guarantee multi-tenant row isolation.
