
Shadow mode is parallel execution without user impact.
# gateway — shadow config
# infra/migration/phases/phase-3-canary/traffic-splits/<namespace-1>-split.conf

upstream <namespace-1>-old {
    server <namespace-1>-old.internal:8080;
    keepalive 64;
}

upstream <namespace-1>-new {
    server <namespace-1>-new.<namespace-1>.svc.cluster.local:8080;
    keepalive 64;
}

server {
    location /api/ {
        # Primary — real response
        proxy_pass http://<namespace-1>-old;

        # Shadow — fire and forget, response discarded
        mirror /shadow-<namespace-1>;
        mirror_request_body on;
    }

    location = /shadow-<namespace-1> {
        internal;
        proxy_pass http://<namespace-1>-new;

        # Shadow MUST NOT reach paid external endpoints
        # handled by egress NetworkPolicy on new namespace:
        # external vendor calls blocked during SHADOWED state
    }
}

Shadow Validation Criteria

# migration/phases/phase-3-canary/shadow-validation.yaml
# Both conditions must hold for 48h before proceeding to canary

<namespace-1>:
  shadow_error_rate_vs_primary:
    threshold: within 1%
    window: 48h
  shadow_latency_p99_vs_primary:
    threshold: within 20%
    window: 48h
  shadow_connection_refused:
    threshold: 0
    window: 48h
  shadow_tls_handshake_failures:
    threshold: 0
    window: 48h

If shadow fails validation → investigate before canary. Do not proceed.
