infra-migration/
│
├── README.md                          ← migration philosophy
│                                         you do not move services
│                                         you redirect traffic with revert capability
│
├── state/
│   ├── registry.yaml                  ← every service, exactly one state
│   │                                     states: UNMAPPED → AUDITED → BASELINED
│   │                                            → SHADOWED → REDIRECTED → DRAINING
│   │                                            → STABLE
│   │                                     no service is between states
│   │
│   └── dependency-order.yaml          ← derived from network/topology/dependency-graph
│                                         leaves migrate first
│                                         gateway migrates last
│
├── audit/
│   ├── per-service/
│   │   └── <service-name>/
│   │       ├── CONTRACT               ← copy from network/contracts/<service>/
│   │       │                             confirmed against actual behavior
│   │       ├── baseline-metrics       ← p50/p95/p99 latency, error rate, rps
│   │       │                             minimum 7 days of data
│   │       │                             this is your rollback reference
│   │       └── known-issues           ← existing bugs before migration
│   │                                     migration must not be blamed for these
│   │
│   └── shared/
│       ├── data-inventory             ← every data store, owner, access pattern
│       ├── hardcoded-ips              ← list of all hardcoded IPs found
│       │                                 each is a migration risk
│       └── ttl-audit                  ← current DNS TTL values
│                                         must be reduced before migration starts
│
├── phases/
│   ├── phase-0-audit/
│   │   └── checklist                  ← gates that must pass before phase-1
│   │                                     no phase transition without checklist sign-off
│   │
│   ├── phase-1-observe/
│   │   ├── checklist
│   │   └── what-to-instrument         ← observability deployed passively
│   │                                     no traffic change in this phase
│   │
│   ├── phase-2-shadow/
│   │   ├── checklist
│   │   ├── comparison-criteria        ← what shadow must match vs primary
│   │   │                                 error rate, status codes, latency range
│   │   └── per-service/
│   │       └── <service-name>/
│   │           └── shadow-config      ← how shadow is configured for this service
│   │                                     fire-and-forget, response discarded
│   │                                     paid external egress BLOCKED in shadow
│   │
│   ├── phase-3-redirect/
│   │   ├── checklist
│   │   ├── traffic-caps/
│   │   │   └── <service-name>/
│   │   │       └── cap-config         ← absolute RPS cap on new infra
│   │   │                                 NOT percentage — absolute number
│   │   │                                 based on synthetic validation results
│   │   │                                 overflow → old infra automatically
│   │   │
│   │   └── per-service/
│   │       └── <service-name>/
│   │           └── redirect-config    ← how traffic is split/redirected
│   │                                     runtime-agnostic description
│   │                                     translated by runtime-adapters
│   │
│   └── phase-4-drain/
│       ├── checklist
│       └── per-service/
│           └── <service-name>/
│               └── drain-config       ← drain window (minimum 7 days)
│                                         old infra stays alive as overflow
│                                         not as rollback — as live overflow
│
├── data/
│   ├── strategy.md                    ← data migrates AFTER traffic is stable
│   │                                     never migrate data and traffic simultaneously
│   │
│   ├── per-service/
│   │   └── <service-name>/
│   │       ├── export-procedure       ← how data is extracted from old store
│   │       ├── transform-procedure    ← if schema changes — document exactly
│   │       ├── import-procedure       ← how data lands in new store
│   │       ├── verify-procedure       ← row counts, checksums, spot checks
│   │       └── rollback-procedure     ← how to revert data if verify fails
│   │                                     this is the ONLY place rollback exists
│   │                                     traffic rollback = redirect config change
│   │                                     data rollback = restore from snapshot
│   │
│   └── shared/
│       ├── snapshot-policy            ← when snapshots are taken
│       │                                 must be: immediately before data migration
│       │                                 not scheduled — on-demand before each step
│       └── integrity-checks           ← what passes = data migration succeeded
│
├── security/
│   ├── data-in-transit/
│   │   └── policy                     ← encryption required on all data movement
│   │                                     source → destination always encrypted
│   │                                     no plaintext data migration
│   │
│   ├── data-at-rest/
│   │   └── policy                     ← encryption state before and after
│   │                                     must be equal or better post-migration
│   │
│   ├── access-during-migration/
│   │   └── policy                     ← who can access what during migration window
│   │                                     principle: minimum access, time-bounded
│   │                                     revoked immediately after phase completes
│   │
│   └── audit-log/
│       └── policy                     ← every migration action logged
│                                         who did what, when, what changed
│                                         immutable — append only
│
├── gates/
│   ├── spike-check                    ← blocks migration if traffic spike detected
│   │                                     migration steps blocked during spike
│   │                                     and 30 minutes post-spike
│   │
│   ├── error-rate-check               ← compares live error rate to baseline
│   │                                     any increase = migration step blocked
│   │
│   ├── data-integrity-check           ← runs after every data migration step
│   │                                     checksums, row counts, spot samples
│   │
│   └── bridge-expiry-check            ← fails if any bridge policy is past expiry
│                                         runs in CI on every commit
│
├── bridges/
│   └── <service-A>-to-<service-B>/
│       ├── config                     ← allows old infra to reach new infra
│       │                                 or new infra to reach unmigrated service
│       └── metadata                   ← created date, expiry date, ticket ref
│                                         bridge without expiry = not allowed
│
├── runbooks/
│   ├── traffic-rollback.md            ← how to revert a redirect in < 2 minutes
│   │                                     step by step, no assumptions
│   │                                     tested in staging before prod migration
│   │
│   ├── data-rollback.md               ← how to restore data from snapshot
│   │                                     which snapshot, how to verify restore
│   │
│   ├── emergency-bypass.md            ← if migration tooling itself fails
│   │                                     manual steps, who to contact
│   │
│   └── freeze-and-hold.md             ← how to freeze all migration activity
│                                         what creates a freeze
│                                         what clears a freeze
│
└── runtime-adapters/
    ├── <runtime-A>/                   ← how redirect-config translates to this runtime
    │   ├── phase-2-shadow/            ← shadow implementation for this runtime
    │   ├── phase-3-redirect/          ← traffic split implementation
    │   └── phase-4-drain/             ← drain implementation
    │
    ├── <runtime-B>/
    │   └── ... same structure
    │
    └── README.md                      ← phases/ describes WHAT to do
                                          runtime-adapters/ describes HOW in each runtime
                                          same phase, different runtimes = different adapter
                                          same correctness guarantee either way