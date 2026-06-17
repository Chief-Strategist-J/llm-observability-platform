PERMISSIVE mode:  accepts both mTLS and plaintext
This deserves its own section because getting it wrong locks out all traffic.

STRICT mode:      rejects plaintext — only mTLS

Migration order:
  Step 1: Deploy sidecar to new namespace (PERMISSIVE)
  Step 2: Verify sidecar is intercepting traffic (check istio-proxy logs)
  Step 3: Switch to STRICT on new namespace only
  Step 4: Verify old → new calls still work (they use bridge, plaintext allowed by bridge)
  Step 5: Deploy sidecar to calling services
  Step 6: Verify mTLS handshake in mesh telemetry
  Step 7: Remove PERMISSIVE exception, all namespaces STRICT

# Phase 2 — PERMISSIVE on new namespace
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: migration-permissive
  namespace: <namespace-1>
  annotations:
    migration.io/temporary: "true"
    migration.io/remove-when: "all callers have sidecars"
spec:
  mtls:
    mode: PERMISSIVE

---
# Phase 6 — STRICT, migration complete
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: <namespace-1>
spec:
  mtls:
    mode: STRICT

Never flip PERMISSIVE → STRICT without first verifying in mesh telemetry that all active connections are already using mTLS. One plaintext caller will get immediately rejected.

Migration Dashboard

# observability/dashboards/migration-progress.json (structure)

panels:
  - title: "Migration State per Service"
    type: table
    columns: [service, state, traffic_split, days_in_state, owner]

  - title: "Canary Error Rate vs Baseline"
    type: graph
    shows: [new_error_rate, old_error_rate, baseline_error_rate]
    alert_threshold: baseline + 0.5%

  - title: "p99 Latency — New vs Old vs Baseline"
    type: graph
    shows: [new_p99, old_p99, baseline_p99]

  - title: "Connection Refused Count"
    type: stat
    alert_on: any > 0

  - title: "Active Bridge Policies"
    type: table
    columns: [bridge_name, expires, ticket, days_remaining]
    alert_on: days_remaining < 14

  - title: "Rollback Events"
    type: table
    columns: [service, phase, timestamp, reason, resolved_in_minutes]

This dashboard is the primary tool during any active migration. It is always open during a canary shift.

The Migration Invariants — Never Violated

1. No service transitions from CANARY → DRAINING without 24h at 100% canary

2. No service transitions from DRAINING → STABLE without 7 days clean drain

3. No bridge policy exists without an expiry date and a ticket

4. No manual network policy change in production — everything through gitops

5. DNS TTL must be 60s before any migration step that involves DNS

6. Rollback must be tested in staging before canary starts in production

7. Observability must be confirmed working before canary starts — 
   if you can't see the metrics, you cannot safely run the canary

8. Old infra is never terminated while any rollback event is unresolved

9. mTLS mode never flips PERMISSIVE → STRICT without mesh telemetry 
   confirming 100% of connections are already mTLS

10. Decommission script is the only path to STABLE — 
    no manual state.yaml edits allowed