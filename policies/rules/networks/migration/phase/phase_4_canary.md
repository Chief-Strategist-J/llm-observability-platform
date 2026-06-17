Traffic split. Real users. Controlled percentage.
# infra/migration/phases/phase-3-canary/traffic-splits/<namespace-1>-split.conf

# Consistent hashing — same user always hits same backend
# Prevents session issues during split
split_clients "${remote_addr}" $<namespace-1>_backend {
    5%    "<namespace-1>-new";    # week 1
    *     "<namespace-1>-old";
}

# Promote by editing this file only:
# 5% → 10% → 25% → 50% → 100%
# Each step requires 24h stability at previous level

Canary Promotion Gate

#!/bin/bash
# migration/scripts/traffic-shift.sh
# Usage: ./traffic-shift.sh <namespace-1> 10
# Shifts <namespace-1> canary to 10%

SERVICE=$1
TARGET_PCT=$2
CURRENT_PCT=$(get_current_split "$SERVICE")   # reads from split.conf

# Gate checks before allowing promotion
check_error_rate "$SERVICE" "$BASELINE_FILE"
check_latency "$SERVICE" "$BASELINE_FILE"
check_refused_connections "$SERVICE"

if [[ $? -ne 0 ]]; then
  echo "Gate check FAILED for $SERVICE at ${CURRENT_PCT}%"
  echo "Cannot promote to ${TARGET_PCT}%"
  echo "Check: infra/observability/dashboards/migration-progress.json"
  exit 1
fi

# Apply split
sed -i "s/${CURRENT_PCT}%.*${SERVICE}-new/${TARGET_PCT}%    \"${SERVICE}-new\"/" \
  "infra/migration/phases/phase-3-canary/traffic-splits/${SERVICE}-split.conf"

nginx -s reload

echo "Promoted $SERVICE: ${CURRENT_PCT}% → ${TARGET_PCT}%"
echo "Monitor for 24h before next promotion"
echo "Rollback: ./traffic-shift.sh $SERVICE $CURRENT_PCT"

Canary Promotion Schedule
Day 0:  5%   → monitor 24h
Day 1:  10%  → monitor 24h
Day 3:  25%  → monitor 48h  (higher stakes, longer window)
Day 5:  50%  → monitor 48h
Day 7:  100% → enter DRAINING state, old still up
Day 14: decommission old if no rollbacks
Any gate failure resets the schedule. Not resets the percentage — resets the clock. You stay at current percentage until 24h clean, then resume.
