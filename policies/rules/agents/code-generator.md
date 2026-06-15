---
trigger: manual
agent: code-generator
role: Senior Implementation Engineer Agent
---

# Code Generator Agent — Policy

## Purpose
The Code Generator Agent is the **only agent that writes and modifies files**. It implements features,
fixes bugs, and produces tests. It strictly follows ALL project policies before writing a single line of code.

It operates in the following order every time:
1. Read `logs/change.log` (last entries) to understand current state
2. Read `policies/rules/critical.rule.md` to load non-negotiables
3. Read the relevant package structure to understand existing code
4. Update contracts FIRST
5. Implement migrations SECOND (if DB changes needed)
6. Write source code THIRD
7. Write tests FOURTH
8. Update `logs/change.log` LAST

---

## Mandatory Pre-flight Checks

Before writing ANY file, the agent MUST:

- [ ] Check `logs/change.log` for the last state of the affected packages
- [ ] Check `logs/memory.log` if a memory save was requested
- [ ] Read the existing `contracts/` for the target package
- [ ] Read the existing `src/shared/ports/` to reuse existing port interfaces
- [ ] Read the existing `src/infra/adapters/` to avoid duplicating adapter code
- [ ] Confirm the correct branch is checked out

---

## Implementation Order (STRICT)

```
1. contracts/          ← write or update FIRST — no src/ file before this
2. database/migrations/ ← write SECOND if schema changes needed
3. src/shared/ports/   ← update or create port interfaces THIRD
4. src/infra/adapters/ ← implement adapters FOURTH
5. src/features/       ← implement feature service/index/types FIFTH
6. src/api/            ← implement REST/event/gRPC handlers SIXTH
7. tests/              ← write all tests SEVENTH
8. logs/change.log     ← update LAST — never skip this step
```

---

## Architecture Rules (enforced on every file written)

### Package Isolation
- NEVER import from another package's `src/`
- All cross-package calls through generated clients in `src/infra/clients/`
- `{lang}-shared/` only for pure types and IO-free utils

### Hexagonal Architecture
```
src/
├── api/          ← Entry-point adapters only. Zero business logic.
│   ├── rest/v1/  ← Maps HTTP → service via index
│   └── events/   ← Maps Kafka message → handler
├── features/     ← ALL business logic. Zero IO. Zero HTTP.
│   └── {name}/
│       ├── index.py     ← public surface only
│       ├── service.py   ← pure logic, no IO
│       ├── repository.py ← data access via port interface only
│       └── types.py     ← all types for this feature
├── infra/        ← All IO implementations
│   └── adapters/ ← Implements port interfaces, all IO here
└── shared/       ← Package-internal only
    └── ports/    ← Protocol interfaces (no implementation)
```

### Temporal Workflow Rules (CRITICAL)
```python
# FORBIDDEN inside @workflow.defn:
datetime.now()          # use workflow.now()
random.random()         # use workflow.random()
uuid4()                 # forbidden
any_http_call()         # must be in activity
any_db_query()          # must be in activity
time.sleep()            # use asyncio with SDK timer

# REQUIRED:
@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, input: MyInput) -> MyOutput:
        result = await workflow.execute_activity(
            my_activity,
            MyActivityInput(...),
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
```

### Activity Rules
```python
@activity.defn
async def my_activity(input: MyActivityInput) -> MyActivityOutput:
    # Idempotent: safe to retry
    # All IO here: DB, HTTP, Redis, Kafka
    # Declare heartbeat if >10 seconds
    # Use idempotency keys for external side effects
```

---

## File Writing Standards

### Python Style
```python
from __future__ import annotations           # always first
from typing import Protocol                  # for port interfaces
from dataclasses import dataclass            # for data types
import logging                               # structured logging

logger = logging.getLogger(__name__)         # module-level logger
```

### Port Interface Pattern
```python
from typing import Protocol

class MyPort(Protocol):
    def do_something(self, input: MyInput) -> MyOutput: ...
    def get_something(self, id: str) -> MyOutput | None: ...
```

### Adapter Implementation Pattern
```python
class MyAdapter:                             # no base class, implements Protocol structurally
    def __init__(self, dependency: DepType) -> None:
        self._dep = dependency

    def do_something(self, input: MyInput) -> MyOutput:
        with tracer.start_as_current_span("adapter.do_something"):
            # all IO here
            ...
```

### Test Pattern
```python
# Unit tests: pure, no IO
def test_my_feature_unit() -> None:
    fake_port = FakeMyPort(...)              # use fakes, not mocks where possible
    result = my_service_function(fake_port)
    assert result == expected

# Integration tests: real infra
@pytest.mark.integration
def test_my_feature_integration(real_db) -> None:
    ...
```

---

## Directory Creation Rules

- Every new directory MUST have a `.gitkeep` file if it starts empty
- Follow package structure exactly — no ad-hoc directories
- New packages: copy structure from an existing package as reference

---

## Change Log Update Format (MANDATORY after every change)

Append to `logs/change.log`:

```
[{ISO-8601-TIMESTAMP}] {one line summary ≤ 80 chars}
└── File: {comma-separated file paths}
    ├── Choice: {why this decision was made}
    └── Changes:
        ├── {feature/component} -> {what changed}
        └── {affected files} → {what is affected}
```

Example:
```
[2026-06-15T08:00:00+05:30] Add HIGH_PERPLEXITY flag to composite scorer
└── File: packages/python/quality-engine/src/handlers/span_quality/composite_scorer.py
    ├── Choice: Include perplexity as 4th weight (0.10) in renormalized composite per Phase 3 spec
    └── Changes:
        ├── composite_scorer.py -> Add perplexity weight, normalize contribution, clamp to [0,1]
        └── tests/unit/test_composite_scorer.py → Add test for 4-weight and 3-weight (perplexity=None) paths
```

---

## Commit Rules

- One commit = one logical change (not mixed)
- `git add -p` for selective staging — NEVER `git add .`
- Commit message format (from `commit-message-git.md`):
  ```
  [feature-ST-01 | Previous State]
     |
     +-- [feature-IN-01 | Input]
         |
         +-- [feature-PR-01 | Processing]
             |
             +-- [feature-DC-01 | Decision]
                 |-- [affected | before | after]
                 `-- [feature-OUT-01 | Output]
                     |
                     `-- [feature-CS-01 | Current State]
  ```
- Types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`
- Subject ≤ 50 chars
- Body: WHY it changed

---

## Worker Registry Update (MANDATORY for new workers)

When creating a new worker, update BOTH:

1. `packages/python/{worker-name}/worker-registry.yaml` (package-local)
2. `registry/workers/{worker-name}.yaml` (global)

Format (from `worker/core-rules.md`):
```yaml
workers:
  - name: my-new-worker
    type: temporal | queue | cron | event
    language: python
    task_queue: my-task-queue          # unique, never shared
    owner: "@team-name"
    stage: 1
    workflows:
      - WorkflowName
    activities:
      - ActivityName
```

---

## Security Rules

- No secrets, passwords, tokens in any file
- `.env.example` with placeholder values (e.g. `REDIS_URL=redis://localhost:6379/0`)
- Actual `.env` listed in `.gitignore`
- Database credentials via environment variables only

---

## Policies to Read Before Starting

| Priority | File | When |
|---|---|---|
| ALWAYS | `policies/rules/critical.rule.md` | Every task |
| ALWAYS | `logs/change.log` (last 50 lines) | Every task |
| Package work | `policies/rules/folderStructure/package-structure.md` | New packages |
| Feature work | `policies/rules/folderStructure/feature-anatomy.md` | New features |
| API work | `policies/rules/folderStructure/api-structure.md` | New endpoints |
| Worker work | `policies/rules/worker/core-rules.md` | New workers |
| Temporal work | `policies/rules/worker/listOfWorkersTypes/temporal-workflow-rules.md` | Temporal code |
| DB work | `policies/rules/database/migration.md` | Schema changes |
| Commit | `policies/rules/git/commit-message-git.md` | Every commit |

---

## Non-Negotiables (will cause immediate rejection by Policy Guardian)

| # | Violation | Consequence |
|---|---|---|
| 1 | Cross-package source import | Code rejected |
| 2 | IO inside Temporal workflow | Code rejected |
| 3 | Missing `worker-registry.yaml` update | Code rejected |
| 4 | `src/` written before `contracts/` | Code rejected |
| 5 | `logs/change.log` not updated | Code rejected |
| 6 | `git add .` used | Commit rejected |
| 7 | Secret in committed file | Emergency rollback |
| 8 | Shared DB between packages | Architecture violation |
