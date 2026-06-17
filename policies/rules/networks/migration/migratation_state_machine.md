
┌─────────┐
│ UNMAPPED│  ← service exists, not yet inventoried
└────┬────┘
     │ audit complete
     ▼
┌─────────┐
│ AUDITED │  ← network contract documented, deps mapped
└────┬────┘
     │ baseline metrics collected (min 7 days)
     ▼
┌──────────────┐
│ BASELINED    │  ← error rates, latency p50/p95/p99 known
└──────┬───────┘
       │ bridge policy applied, observability deployed
       ▼
┌──────────────┐
│ BRIDGED      │  ← reachable from new infra, still running on old
└──────┬───────┘
       │ shadow mode validated (48h minimum)
       ▼
┌──────────────┐
│ SHADOWED     │  ← new infra receiving shadow traffic, errors compared
└──────┬───────┘
       │ canary started (5%)
       ▼
┌──────────────┐
│ CANARY       │  ← live traffic split active, error rate monitored
└──────┬───────┘
       │ canary stable at 100%
       ▼
┌──────────────┐
│ DRAINING     │  ← old infra receiving 0% traffic but still up
└──────┬───────┘
       │ 7 days at 0%, no rollbacks triggered
       ▼
┌──────────────┐
│ MIGRATED     │  ← new infra only, old infra still exists
└──────┬───────┘
       │ old infra decommissioned, bridge removed
       ▼
┌──────────────┐
│ STABLE       │  ← migration complete
└──────────────┘


Rollback Contracts — Every Phase

Phase 0 — Audit
  Rollback: nothing deployed, nothing to rollback

Phase 1 — Observe
  Rollback: kubectl delete -f otel-passive-config.yaml
  Time:     <30 seconds

Phase 2 — Bridge
  Rollback: kubectl delete -f migration/bridges/<service>-bridge.yaml
  Time:     <10 seconds
  Effect:   new infra can no longer reach old service (safe — new has no traffic yet)

Phase 3 — Shadow
  Rollback: remove mirror directive from nginx, nginx -s reload
  Time:     <30 seconds
  Effect:   shadow traffic stops, primary unaffected

Phase 4 — Canary (at any percentage)
  Rollback: set split back to 0%, nginx -s reload
  Time:     <30 seconds
  Effect:   100% traffic returns to old infra immediately

Phase 5 — Drain
  Rollback: set split back to 50/50 or 100% old, nginx -s reload
  Time:     <30 seconds
  Old infra still running — this is why drain window exists

Phase 6 — Decommission
  Rollback: NONE — this is the point of no return
  Gate:     script enforces 7-day drain + zero rollbacks before allowing this