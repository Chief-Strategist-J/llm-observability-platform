Old infra at 0% traffic. Still running. Watched.

# migration/phases/phase-4-drain/drain-configs/<namespace-1>-drain.yaml

drain_started: 2024-04-01
drain_window: 7d
service: <namespace-1>

old_infra:
  traffic_pct: 0
  status: running             ← still up, not terminated
  termination_blocked_until: 2024-04-08

new_infra:
  traffic_pct: 100
  status: running
  health: nominal

rollback_trigger:
  error_rate_threshold: baseline + 0.5%
  latency_p99_threshold: baseline × 1.5
  auto_rollback: false        ← manual decision, not automated
  notify: [slack-infra-channel]

During drain: old infra handles zero traffic but is one nginx reload away from resuming. This is your insurance policy.
