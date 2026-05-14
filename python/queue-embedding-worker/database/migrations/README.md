# Migration Strategy

- **Forward-only migrations**: each file is immutable once merged.
- **Naming**: `NNN_<description>.sql`.
- **Deploy order**: sorted lexicographically.
- **Rollback strategy**: prefer compensating migration (do not edit existing migration).
- **Operational strategy**: run migrations before worker rollout; worker is backward-compatible for one migration window.
