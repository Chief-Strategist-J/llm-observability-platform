infra-network/
│
├── README.md                          ← what this folder owns and does NOT own
│
├── topology/
│   ├── segments.md                    ← defines every network segment by name
│   │                                     segment = logical isolation boundary
│   │                                     example: segment-public, segment-internal,
│   │                                              segment-data, segment-observability
│   │
│   ├── trust-model.md                 ← who trusts whom and why
│   │                                     explicit: segment-A trusts segment-B on port X
│   │                                     default: no trust
│   │
│   └── dependency-graph.md            ← which segment calls which
│                                         used to derive firewall rules
│                                         and migration order
│
├── dns/
│   ├── zones/
│   │   ├── internal/                  ← service discovery names
│   │   │   └── <segment-name>/        ← one zone file per segment
│   │   └── external/                  ← public DNS (separate concern)
│   │
│   ├── split-horizon/                 ← same name resolves differently
│   │   └── rules/                     ← inside vs outside resolution
│   │
│   └── ttl-policy.md                  ← TTL values per record type
│                                         CRITICAL: must be set before migration
│
├── tls/
│   ├── strategy.md                    ← termination points, cert rotation policy
│   │                                     who terminates, where, what CA
│   │
│   ├── internal/                      ← mTLS between services
│   │   ├── ca/                        ← internal CA config (not certs)
│   │   └── rotation-policy.md
│   │
│   └── external/                      ← public-facing TLS
│       └── renewal-policy.md
│
├── isolation/
│   ├── policy-model.md                ← default-deny-all documented here
│   │                                     the rule: deny everything, allow explicitly
│   │
│   ├── per-segment/
│   │   └── <segment-name>/
│   │       ├── ingress-policy         ← what can reach this segment
│   │       ├── egress-policy          ← what this segment can reach
│   │       └── internal-policy        ← within-segment rules
│   │
│   └── shared/
│       ├── allow-dns                  ← DNS egress — every segment needs this
│       ├── allow-observability        ← metrics scrape ingress — passive only
│       └── allow-health-checks        ← health check port — separate from traffic
│
├── firewall/
│   ├── base/                          ← rules that apply everywhere
│   │   ├── default-deny
│   │   └── allow-established
│   │
│   ├── per-segment/
│   │   └── <segment-name>/            ← segment-specific rules
│   │                                     maps directly from isolation/per-segment
│   │
│   └── egress/
│       └── external-allowlist         ← explicit external endpoints allowed
│                                         everything else blocked
│
├── contracts/
│   └── <service-name>/
│       └── CONTRACT                   ← declares:
│                                         - listens on which ports
│                                         - calls which services on which ports
│                                         - needs which external endpoints
│                                         - does NOT need (explicit exclusions)
│                                         CI fails if this diverges from policies
│
└── runtime-adapters/
    ├── <runtime-A>/                   ← e.g. docker, k8s, vm, bare-metal
    │   └── apply-isolation/           ← how to apply isolation/ policies
    │                                     in this specific runtime
    │                                     the policy is runtime-agnostic
    │                                     this folder is the translation layer
    │
    ├── <runtime-B>/
    │   └── apply-isolation/
    │
    └── README.md                      ← isolation/ is the source of truth
                                          runtime-adapters/ is just translation