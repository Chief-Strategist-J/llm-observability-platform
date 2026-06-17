Bridge policies let new infra reach services still on old infra. Nothing moves yet.
# migration/bridges/<namespace-1>-to-<namespace-3>-bridge.yaml
# PURPOSE: Allow <namespace-1> on new k8s to reach <namespace-3> still on legacy
# CREATED: 2024-03-10
# EXPIRES: 2024-06-30
# TICKET: INFRA-4821
# REMOVE WHEN: <namespace-3> reaches STABLE state

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: bridge-<namespace-1>-to-<namespace-3>
  namespace: <namespace-3>          # policy lives in the TARGET namespace
  annotations:
    migration.io/bridge: "true"
    migration.io/expires: "2024-06-30"
    migration.io/ticket: "INFRA-4821"
    migration.io/direction: "<namespace-1> → <namespace-3>"
spec:
  podSelector:
    matchLabels:
      app: <namespace-3>
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: <namespace-1>-new    # new namespace label
      ports:
        - protocol: TCP
          port: 9090

Bridge Expiry Check — CI Step

#!/bin/bash
# migration/scripts/check-bridge-expiry.sh
# Fails CI if any bridge policy is past its expiry date

TODAY=$(date +%Y-%m-%d)
FAILED=0

for file in $(find infra/migration/bridges -name "*.yaml"); do
  EXPIRES=$(grep 'migration.io/expires' "$file" | awk -F'"' '{print $2}')
  TICKET=$(grep 'migration.io/ticket' "$file" | awk -F'"' '{print $2}')

  if [[ "$EXPIRES" < "$TODAY" ]]; then
    echo "EXPIRED BRIDGE: $file"
    echo "  Expired: $EXPIRES"
    echo "  Ticket:  $TICKET"
    echo "  Action:  Decommission or extend with updated ticket"
    FAILED=1
  fi
done

exit $FAILED