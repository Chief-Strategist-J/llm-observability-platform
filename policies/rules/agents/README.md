# Agent Policies

This directory defines the system prompt, roles, responsibilities, and strict rules
for each AI agent deployed in this project.

---

## Agents

| Agent | File | Role | Can Write? |
|---|---|---|---|
| **Code Reviewer** | [code-reviewer.md](./code-reviewer.md) | Audits code against all policies before merge | ❌ Read-only |
| **Policy Guardian** | [policy-guardian.md](./policy-guardian.md) | Validates compliance of plans and implementations | ❌ Read-only |
| **Code Generator** | [code-generator.md](./code-generator.md) | Implements features following all policies | ✅ Writes code |

---

## Agent Invocation Order

```
[User Request]
      │
      ▼
[Policy Guardian]          ← Reads ALL policies, validates the plan
      │ COMPLIANCE REPORT
      ▼
[Code Generator]           ← Implements: contracts → migrations → ports → adapters → features → api → tests → changelog
      │ IMPLEMENTATION_COMPLETE
      ▼
[Code Reviewer]            ← Audits all written files against policies
      │ APPROVED | CHANGES_REQUIRED
      ▼
[Code Generator]           ← Applies fixes if CHANGES_REQUIRED
      │
      ▼
[Commit & Push]            ← One commit per logical change, git add -p, ASCII decision tree message
```

---

## Non-Negotiables (shared across all agents)

These rules are absolute — no exception, no override:

1. **No cross-package source imports** — packages are hermetically isolated
2. **No IO inside Temporal workflow definitions** — all IO in activities
3. **`worker-registry.yaml` must be updated** for every new worker
4. **Contracts written before implementation** — no src/ before contracts/
5. **`logs/change.log` updated after every change** — with timestamp + ASCII tree
6. **No `git add .`** — always `git add -p` for selective staging
7. **No secrets in committed files** — `.env.example` with placeholders only
8. **Shared databases between packages are forbidden**
9. **Activities must be idempotent** — safe to retry
10. **Every worker emits OTEL spans** — no worker ships without tracing
