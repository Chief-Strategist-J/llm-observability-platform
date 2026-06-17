infra/
├── gateway/
│   ├── nginx/
│   │   ├── nginx.conf
│   │   ├── conf.d/
│   │   │   ├── upstream.conf
│   │   │   ├── rate-limit.conf
│   │   │   ├── ssl.conf
│   │   │   └── proxy-headers.conf
│   │   └── vhosts/
│   │       ├── api.<domain>.conf
│   │       └── internal.conf
│   ├── envoy/
│   │   ├── envoy.yaml
│   │   └── clusters/
│   │       ├── <service-a>-cluster.yaml
│   │       ├── <service-b>-cluster.yaml
│   │       └── <service-n>-cluster.yaml
│   └── apigw/
│       ├── declarative/
│       │   ├── routes.yaml
│       │   ├── plugins.yaml
│       │   └── consumers.yaml
│       └── scripts/
│           └── sync.sh
│
├── network/
│   ├── dns/
│   │   ├── internal-zones.conf
│   │   └── split-horizon.conf
│   ├── vpn/
│   │   └── wireguard/
│   │       ├── wg0.conf
│   │       └── peers/
│   │           ├── <node-1>.conf
│   │           └── <node-n>.conf
│   ├── firewall/
│   │   ├── base-rules.nft
│   │   ├── service-rules/
│   │   │   └── <service-name>.nft      ← one file per service
│   │   └── egress-policy.nft
│   └── load-balancer/
│       ├── haproxy.cfg
│       └── health-checks/
│           └── <service-name>.cfg
│
├── k8s/
│   ├── namespaces/
│   │   ├── <namespace-1>/
│   │   │   └── namespace.yaml
│   │   ├── <namespace-2>/
│   │   │   └── namespace.yaml
│   │   ├── <namespace-n>/
│   │   │   └── namespace.yaml
│   │   ├── gateway/
│   │   │   └── namespace.yaml
│   │   └── observability/
│   │       └── namespace.yaml
│   │
│   ├── network-policies/
│   │   ├── base/
│   │   │   ├── default-deny-all.yaml          ← applied to ALL namespaces
│   │   │   ├── allow-dns.yaml                 ← kube-dns egress, all namespaces
│   │   │   └── allow-mesh-control-plane.yaml  ← istiod/linkerd control plane
│   │   ├── gateway/
│   │   │   └── allow-gateway-ingress.yaml
│   │   ├── observability/
│   │   │   └── allow-scrape-ingress.yaml
│   │   └── per-namespace/
│   │       ├── <namespace-1>/
│   │       │   ├── allow-ingress.yaml
│   │       │   ├── allow-egress.yaml
│   │       │   └── allow-internal.yaml
│   │       ├── <namespace-2>/
│   │       │   ├── allow-ingress.yaml
│   │       │   ├── allow-egress.yaml
│   │       │   └── allow-internal.yaml
│   │       └── <namespace-n>/
│   │           ├── allow-ingress.yaml
│   │           ├── allow-egress.yaml
│   │           └── allow-internal.yaml
│   │
│   └── services/
│       ├── <namespace-1>/
│       │   ├── deployment.yaml
│       │   ├── service.yaml
│       │   ├── hpa.yaml
│       │   └── CONTRACT.md
│       ├── <namespace-2>/
│       │   ├── deployment.yaml
│       │   ├── service.yaml
│       │   ├── hpa.yaml
│       │   └── CONTRACT.md
│       └── <namespace-n>/
│           ├── deployment.yaml
│           ├── service.yaml
│           ├── hpa.yaml
│           └── CONTRACT.md
│
├── service-mesh/
│   ├── control-plane/
│   │   └── config.yaml
│   ├── mtls/
│   │   ├── peer-auth/
│   │   │   ├── <namespace-1>-peer-auth.yaml
│   │   │   ├── <namespace-2>-peer-auth.yaml
│   │   │   └── <namespace-n>-peer-auth.yaml
│   │   └── destination-rules/
│   │       ├── <namespace-1>-dr.yaml
│   │       └── <namespace-n>-dr.yaml
│   └── traffic/
│       ├── virtual-services/
│       │   ├── <namespace-1>-vs.yaml
│       │   └── <namespace-n>-vs.yaml
│       └── gateway.yaml
│
├── observability/
│   ├── otel/
│   │   ├── collector-config.yaml
│   │   └── exporters/
│   │       ├── prometheus-exporter.yaml
│   │       └── jaeger-exporter.yaml
│   ├── prometheus/
│   │   ├── rules/
│   │   │   ├── network-alerts.yaml
│   │   │   └── slo-alerts.yaml
│   │   └── scrape-configs/
│   │       └── <namespace-n>-scrape.yaml
│   └── dashboards/
│       ├── network-topology.json
│       └── migration-progress.json     ← dedicated dashboard, explained below
│
└── migration/
    ├── state.yaml                      ← single source of truth, all services
    ├── phases/
    │   ├── phase-0-audit/
    │   │   ├── checklist.md
    │   │   └── baseline-snapshot.yaml
    │   ├── phase-1-observe/
    │   │   ├── checklist.md
    │   │   └── otel-passive-config.yaml
    │   ├── phase-2-bridge/
    │   │   ├── checklist.md
    │   │   └── bridge-policies/
    │   │       └── <namespace-n>-bridge.yaml
    │   ├── phase-3-canary/
    │   │   ├── checklist.md
    │   │   └── traffic-splits/
    │   │       └── <namespace-n>-split.conf
    │   ├── phase-4-drain/
    │   │   ├── checklist.md
    │   │   └── drain-configs/
    │   │       └── <namespace-n>-drain.yaml
    │   └── phase-5-decommission/
    │       ├── checklist.md
    │       └── cleanup/
    │           └── <namespace-n>-cleanup.yaml
    ├── bridges/
    │   └── <namespace-n>-to-<namespace-m>-bridge.yaml
    ├── runbooks/
    │   ├── rollback-gateway.md
    │   ├── rollback-network-policy.md
    │   ├── rollback-dns.md
    │   ├── rollback-mesh.md
    │   └── emergency-bypass.md
    └── scripts/
        ├── check-bridge-expiry.sh
        ├── traffic-shift.sh
        ├── verify-baseline.sh
        ├── drain-service.sh
        └── migration-status.sh