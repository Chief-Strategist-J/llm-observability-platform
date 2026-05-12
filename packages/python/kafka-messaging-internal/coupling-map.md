# Coupling Map - kafka-messaging-internal

## Package Isolation Status
- **Status**: ISOLATED
- **External Dependencies**: None
- **Cross-Package Imports**: None
- **Last Verified**: 2025-01-11

## Internal Coupling Analysis

### Current Violations (Pre-Migration)
#### Layer Call Violations
1. **sdk.py → domain/ports/** (Direct import)
   - Type: CoI (Identity coupling)
   - Severity: P0 - Before any other work
   - Resolution: Wrap behind feature/index

2. **sdk.py → infrastructure/adapters/** (Direct import)
   - Type: CoI (Identity coupling)
   - Severity: P0 - Before any other work
   - Resolution: Use DI container with port interfaces

3. **application/api/v1/*.py → domain/services/** (Direct import)
   - Type: CoI (Identity coupling)
   - Severity: P0 - Before any other work
   - Resolution: API handlers call feature/index only

#### SRP Violations
1. **sdk.py**: Factory + Orchestration + Configuration
   - Type: Mixed responsibilities
   - Resolution: Split into feature services

2. **application/api/v1/*.py**: API + Business + Data Access
   - Type: Mixed responsibilities
   - Resolution: Move business logic to features, data access to repositories

#### Missing Port Interfaces
1. **Direct PostgreSQL Usage**
   - Type: CoI (Identity coupling)
   - Resolution: Implement DatabasePort adapter

2. **Direct MongoDB Usage**
   - Type: CoI (Identity coupling)
   - Resolution: Implement DatabasePort adapter

3. **Direct Schema Registry Usage**
   - Type: CoI (Identity coupling)
   - Resolution: Implement SchemaRegistryPort adapter

## Post-Migration Target State

### Allowed Coupling Paths
```
api/rest/v1/handlers/ → features/*/index.py (ONLY)
features/*/service.py → features/*/repository.py (ONLY)
features/*/repository.py → infra/adapters/*/ (via ports ONLY)
infra/adapters/*/ → vendor SDKs (ONLY)
```

### Forbidden Coupling Paths
```
api/* → features/*/service.py (FORBIDDEN - use index)
api/* → infra/* (FORBIDDEN)
features/*/service.py → infra/* (FORBIDDEN - use ports)
features/A/* → features/B/* (FORBIDDEN)
shared/* → features/* (FORBIDDEN)
scripts/* → src/* (FORBIDDEN - HTTP/CLI only)
```

## Resolution Status

### Completed
- [x] External dependency verification
- [x] Coupling violation documentation
- [x] Contract creation (OpenAPI v1)

### In Progress
- [ ] Port interface implementation
- [ ] Feature service creation
- [ ] API layer refactoring

### Pending
- [ ] Adapter pattern implementation
- [ ] DI container setup
- [ ] Tracing implementation
- [ ] Import guard configuration

## Validation Checklist

### CI Checks
- [ ] Import guards prevent cross-package imports
- [ ] Layer call rules enforced
- [ ] Coupling map accuracy verified
- [ ] Zero coupling violations in main

### Runtime Checks
- [ ] All calls use port interfaces
- [ ] No direct adapter references
- [ ] Feature index pattern followed
- [ ] Tracing spans on all boundaries

## Notes
- This package is completely isolated (no external dependencies)
- All violations are internal and will be resolved during migration
- Coupling map will be updated after each phase completion
- Final state must have zero violations
