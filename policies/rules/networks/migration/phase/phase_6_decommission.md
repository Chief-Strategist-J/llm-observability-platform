Only after drain window closes with zero rollback events.

#!/bin/bash
# migration/scripts/drain-service.sh
# Final decommission sequence — run only when drain window passed cleanly

SERVICE=$1
STATE=$(get_migration_state "$SERVICE")

if [[ "$STATE" != "DRAINING" ]]; then
  echo "ERROR: $SERVICE is not in DRAINING state (current: $STATE)"
  exit 1
fi

DRAIN_SINCE=$(get_drain_start "$SERVICE")
DAYS_DRAINED=$(days_since "$DRAIN_SINCE")

if [[ $DAYS_DRAINED -lt 7 ]]; then
  echo "ERROR: Drain window not complete ($DAYS_DRAINED/7 days)"
  exit 1
fi

ROLLBACKS=$(get_rollback_count "$SERVICE" "$DRAIN_SINCE")
if [[ $ROLLBACKS -gt 0 ]]; then
  echo "ERROR: $ROLLBACKS rollback(s) occurred during drain window"
  echo "Reset drain window and re-evaluate"
  exit 1
fi

echo "All gates passed. Proceeding with decommission of $SERVICE old infra."
echo "Steps:"
echo "  1. Remove bridge policy"
echo "  2. Delete old deployment"
echo "  3. Remove traffic split config"
echo "  4. Update state.yaml → STABLE"
echo "  5. Set DNS TTL back to 300"
echo ""
read -p "Type 'DECOMMISSION $SERVICE' to confirm: " CONFIRM

if [[ "$CONFIRM" != "DECOMMISSION $SERVICE" ]]; then
  echo "Aborted"
  exit 1
fi

# Execute
kubectl delete -f "infra/migration/bridges/${SERVICE}-bridge.yaml"
kubectl delete deployment "${SERVICE}-old" -n "${SERVICE}"
rm "infra/migration/phases/phase-3-canary/traffic-splits/${SERVICE}-split.conf"
update_migration_state "$SERVICE" "STABLE"

echo "Decommission complete. $SERVICE is now STABLE."