# Connascence Compliance for `logIntelligent`

This package now enforces coupling toward CoN and CoT.

## Enforced decisions

- Domain contracts are defined in `domain/ports.py`.
- Flow code in `pipeline.py` depends on contract types, not concrete adapters.
- Adapter wiring is centralized in `dependencies.py` as the single composition root.
- API routes only call a service boundary and do not contain business logic.
- Duplicate algorithm implementation in `infrastructure/observability/server/log_intelligence_pipeline.py` was removed and replaced by re-export from one source.

## Connascence target mapping

- CoN and CoT are primary coupling forms.
- CoM is constrained to explicit DTO fields and domain models.
- CoP is limited by named DTO payloads.
- CoA exists only inside one implementation per algorithm.
- CoE, timing, value, and identity coupling are pushed out of domain flow.

## DRY enforcement

- One pipeline implementation exists in `logIntelligent/pipeline.py`.
- One composition root exists in `logIntelligent/dependencies.py`.
- One API contract definition exists in `logIntelligent/api/schemas.py`.
- Business rules run in service and pipeline layers only.
