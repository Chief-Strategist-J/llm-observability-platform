# Changelog - Budget Provisioner API

## v1.0.0 (2026-05-28)
- Initial release of the Budget Provisioner REST API contract.
- Added CRUD routes:
  - POST /budgets/{user_id}/{model}
  - GET /budgets/{user_id}
  - DELETE /budgets/{user_id}/{model}
  - GET /budgets/{user_id}/{model}/status
- Implemented Bearer JWT authentication scheme.
