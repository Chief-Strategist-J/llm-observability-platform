infra-gateway/
│
├── README.md                          ← what gateway owns and does NOT own
│                                         gateway does NOT own: auth logic,
│                                         business routing, service contracts
│
├── architecture/
│   ├── layers.md                      ← defines the tier model
│   │                                     Layer 1: edge (TLS, DDoS, rate limit)
│   │                                     Layer 2: router (path → service mapping)
│   │                                     Layer 3: auth (token validation only)
│   │                                     each layer has exactly one job
│   │
│   ├── traffic-flow.md                ← how a request moves through layers
│   │                                     draw this. do not leave it implicit.
│   │
│   └── failure-modes.md               ← what happens when each layer fails
│                                         and which layer handles the fallback
│
├── edge/
│   ├── tls/
│   │   └── termination-config         ← where TLS terminates
│   │                                     what ciphers are allowed
│   │                                     HSTS policy
│   │
│   ├── rate-limiting/
│   │   ├── zones/                     ← rate limit zones by traffic type
│   │   │   ├── per-ip                 ← protects against single-source abuse
│   │   │   ├── per-tenant             ← protects against tenant overconsumption
│   │   │   └── per-route              ← protects expensive endpoints specifically
│   │   │
│   │   └── tiers/                     ← different limits for different user tiers
│   │       ├── <tier-name>/
│   │       │   └── limits             ← rps, burst, connection count
│   │       └── default/
│   │           └── limits             ← most restrictive — applies if no tier match
│   │
│   ├── security-headers/
│   │   └── policy                     ← HSTS, CSP, X-Frame-Options, etc.
│   │                                     applied at edge — never at service level
│   │
│   └── request-enrichment/
│       └── policy                     ← what gets injected into every request
│                                         request-id, timestamp, client-ip
│                                         injected ONCE at edge, forwarded downstream
│
├── routing/
│   ├── rules/
│   │   └── <domain-or-context>/
│   │       └── routes                 ← path patterns → upstream service mapping
│   │                                     no business logic here
│   │                                     only: this path goes to this service
│   │
│   ├── upstreams/
│   │   └── <service-name>/
│   │       └── pool-config            ← connection pool settings
│   │                                     health check endpoint
│   │                                     timeout values (MUST be < gateway timeout)
│   │                                     failover behavior
│   │
│   ├── health-checks/
│   │   └── <service-name>/
│   │       └── config                 ← active health check config per upstream
│   │                                     checks health port, not traffic port
│   │
│   └── timeouts/
│       └── hierarchy                  ← documents timeout at each layer
│                                         gateway > service > downstream
│                                         every hop must be smaller than its caller
│
├── auth/
│   ├── strategy.md                    ← auth happens at gateway, not at service
│   │                                     services receive claims, not tokens
│   │                                     services do NOT re-validate tokens
│   │
│   └── flows/
│       └── <auth-type>/               ← e.g. jwt, apikey, mtls, oauth
│           └── flow                   ← how this auth type is validated at gateway
│                                         what headers are injected downstream
│
├── observability/
│   ├── access-log-format              ← structured log format
│   │                                     must include: request-id, upstream,
│   │                                     upstream-latency, status, route
│   │
│   ├── metrics/
│   │   └── what-to-expose             ← rps, error rate, latency p50/p95/p99
│   │                                     per upstream, per route, per tier
│   │
│   └── tracing/
│       └── propagation                ← how trace context is forwarded
│                                         W3C traceparent header standard
│
└── runtime-adapters/
    ├── <proxy-A>/                     ← e.g. nginx, traefik, envoy, apache, caddy
    │   ├── edge/                      ← how edge/ configs map to this proxy
    │   ├── routing/                   ← how routing/ configs map to this proxy
    │   └── README.md                  ← what this proxy supports and what it doesn't
    │
    ├── <proxy-B>/
    │   └── ... same structure
    │
    └── README.md                      ← architecture/ is the source of truth
                                          runtime-adapters/ is translation only
                                          swap proxy by swapping adapter folder