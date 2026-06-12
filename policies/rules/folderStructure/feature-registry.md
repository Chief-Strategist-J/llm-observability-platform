Feature Registry — Tracking All Features in a Package
Every package maintains a feature-registry.yaml at the package root. CI reads this to track feature lifecycle, flag status, and contract versions.

feature-registry.yaml
 
features:
  - name:           payments
    status:         active               # active | deprecated | sunset
    contract:       contracts/v1.yaml
    contract_version: v1
    owner:          @payments-team
    added:          2024-11-01
    flags:
      - name: payments.new-flow
        status: rolling-out
    migrations:
      - 0001_payments_init
    depends_on_features: []
    depends_on_packages: []
 
  - name:           refunds
    status:         active
    contract:       contracts/v1.yaml
    contract_version: v1
    owner:          @payments-team
    added:          2024-12-01
    flags: []
    migrations:
      - 0002_refunds_init
    depends_on_features:
      - payments
    depends_on_packages: []
 
  - name:           legacy-checkout
    status:         deprecated
    deprecated_on:  2025-01-15
    sunset_on:      2025-07-15
    replaced_by:    payments
    owner:          @payments-team

====
How the Package Scales — Adding Features Over Time

Phase
Package Has
Structure Change
Rule
Start
1 feature
features/payments/ added
Full feature anatomy from day one
Growing
2-4 features
features/refunds/, features/disputes/ added
Each feature is independent — no touching existing features
Mature
5-8 features
features/{name}/ for each
If two features share types, extract to src/shared/types/
Large
8+ features
Review feature registry for split signals
Features with no shared state may become separate packages
Split
Cross-package need
New package created, contract published to shared/
Original feature becomes an API consumer of the new package


Cross-Feature Communication Inside One Package

Allowed:
  features/refunds/service → features/payments/index (call via index only)
  features/disputes/service → features/payments/index
 
Not allowed:
  features/refunds/service → features/payments/service (internal bypass)
  features/refunds/repository → features/payments/repository (direct DB cross)
  features/refunds/handler → features/payments/handler (handler to handler)
 
When two features need the same data:
  Option A: feature B calls feature A's index (preferred for logic reuse)
  Option B: both features query the same DB table via their own repository
            (acceptable if the data access is simple and independent)
  Option C: extract a shared sub-service to src/shared/ if the logic
            is truly shared and neither feature owns it

