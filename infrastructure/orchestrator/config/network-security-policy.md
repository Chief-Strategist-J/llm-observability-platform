# Network Security Architecture

## Overview
This document outlines the network security architecture for the LLM Observability Platform infrastructure. The architecture implements defense-in-depth principles through network segmentation, service isolation, and controlled access via a reverse proxy.

## Network Segmentation

### 1. Observability Network (`172.20.0.0/16`)
**Purpose**: Monitoring, logging, and observability stack

**Services**:
- Prometheus (metrics collection)
- Grafana (visualization)
- Loki (log aggregation)
- Tempo (distributed tracing)
- Jaeger (tracing UI)
- OTEL Collector (telemetry pipeline)
- Promtail (log shipping)
- AlertManager (alerting)
- Traefik (reverse proxy - bridge to all networks)

**Access**: External via Traefik with TLS encryption and authentication

**Security**:
- All external access requires HTTPS
- Basic authentication on admin interfaces
- Rate limiting (100 req/s, 50 burst)
- Security headers (HSTS, CSP, XSS protection)

### 2. Data Network (`172.21.0.0/16`)
**Purpose**: Database and data storage services

**Services**:
- MongoDB (document database)
- Redis (cache/session store)
- Neo4j (graph database)
- Qdrant (vector database)
- Mongo Express (MongoDB admin UI - bridged to observability network)

**Access**:
- Internal only for databases (MongoDB, Redis)
- External via Traefik for admin UIs (Mongo Express, Neo4j Browser, Qdrant UI)
- Direct port exposure for database protocols (MongoDB: 27017, Redis: 6379, Neo4j Bolt: 7687, Qdrant gRPC: 6334)

**Security**:
- Database credentials required for all connections
- No direct external access to database ports (except localhost)
- Admin UIs protected by Traefik authentication

### 3. Messaging Network (`172.22.0.0/16`)
**Purpose**: Message streaming and event processing

**Services**:
- Kafka (message broker)

**Access**: Internal only, direct port exposure for broker protocol

**Security**:
- No external access
- Direct ports (9092 broker, 19093 controller) for internal service communication only
- Future: Add SASL authentication and TLS encryption

### 4. CI/CD Network (`172.23.0.0/16`)
**Purpose**: Continuous deployment and GitOps

**Services**:
- ArgoCD Server (GitOps controller)
- ArgoCD Repo Server (repository management)

**Access**: External via Traefik for ArgoCD Server UI

**Security**:
- ArgoCD Server UI accessible via HTTPS with Traefik
- ArgoCD Repo Server internal only
- TLS termination at Traefik

## Access Control Matrix

| Service | Network | External Access | Method | Authentication |
|---------|---------|----------------|--------|----------------|
| **Traefik** | All (bridge) | ✅ Yes | HTTPS :443, HTTP :80 | Basic Auth (dashboard) |
| **Prometheus** | Observability | ✅ Yes | HTTPS via Traefik | Basic Auth |
| **Grafana** | Observability | ✅ Yes | HTTPS via Traefik | Grafana Login |
| **Loki** | Observability | ✅ Yes | HTTPS via Traefik | Basic Auth |
| **Tempo** | Observability | ✅ Yes | HTTPS via Traefik | Basic Auth |
| **Jaeger** | Observability | ✅ Yes | HTTPS via Traefik | None (read-only UI) |
| **OTEL Collector** | Observability | ⚠️ Partial | OTLP ports: 4317, 4318 (direct)<br>Metrics via Traefik | Basic Auth (metrics only) |
| **Promtail** | Observability | ✅ Yes | HTTPS via Traefik | Basic Auth |
| **AlertManager** | Observability | ✅ Yes | HTTPS via Traefik | Basic Auth |
| **MongoDB** | Data | ❌ No | Direct :27017 (localhost only) | MongoDB Auth |
| **Mongo Express** | Data + Observability | ✅ Yes | HTTPS via Traefik | Basic Auth + Mongo Express Auth |
| **Redis** | Data | ❌ No | Direct :6379 (localhost only) | None (add password in production) |
| **Neo4j** | Data + Observability | ⚠️ Partial | Browser UI via Traefik<br>Bolt :7687 (direct) | Neo4j Auth |
| **Qdrant** | Data + Observability | ⚠️ Partial | REST API via Traefik<br>gRPC :6334 (direct) | API Key (future) |
| **Kafka** | Messaging | ❌ No | Direct :9092, :19093 (internal) | None (add SASL in production) |
| **ArgoCD Server** | CI/CD + Observability | ✅ Yes | HTTPS via Traefik | ArgoCD Login |
| **ArgoCD Repo** | CI/CD | ❌ No | Internal only | N/A |

## Security Features

### TLS Encryption
- **Certificate Provider**: Let's Encrypt (ACME staging for development)
- **TLS Version**: Minimum TLS 1.2
- **Cipher Suites**: Secure defaults from Traefik v3.5
- **HTTP Redirect**: All HTTP traffic redirected to HTTPS

### Security Headers
All services routed through Traefik include:
- `Strict-Transport-Security`: Force HTTPS for 1 year
- `X-Frame-Options`: Deny (prevent clickjacking)
- `X-Content-Type-Options`: nosniff
- `X-XSS-Protection`: 1; mode=block
- `Referrer-Policy`: strict-origin-when-cross-origin
- `Permissions-Policy`: Restrict geolocation, microphone, camera
- Remove `Server` and `X-Powered-By` headers

### Rate Limiting
- **Average**: 100 requests/second
- **Burst**: 50 additional requests
- **Period**: 1 second
- Applied to all Traefik-routed services

### IP Whitelisting
- **Allowed Ranges**:
  - `127.0.0.1/32` (localhost)
  - `172.20.0.0/16` (observability network)
  - `172.21.0.0/16` (data network)
  - `172.22.0.0/16` (messaging network)
  - `172.23.0.0/16` (cicd network)
- Can be restricted further per service in production

## Production Hardening Recommendations

### Immediate
1. **Change Default Passwords**: Update all passwords in `.env` file
2. **Generate Strong API Keys**: Replace placeholder API keys
3. **Real TLS Certificates**: Switch from Let's Encrypt staging to production
4. **Redis Password**: Enable `requirepass` in Redis configuration
5. **Kafka SASL**: Implement SASL/PLAIN or SASL/SCRAM authentication

### Short-term
1. **Network Policies**: Implement Docker network policies to restrict inter-service communication
2. **Secrets Management**: Use Docker Secrets or external vault (HashiCorp Vault, AWS Secrets Manager)
3. **Firewall Rules**: Restrict exposed ports at host firewall level
4. **Monitoring**: Alert on failed authentication attempts, unusual traffic patterns
5. **Backup Encryption**: Encrypt database backups at rest

### Long-term
1. **mTLS**: Implement mutual TLS for service-to-service communication
2. **Zero Trust**: Implement service mesh (Istio, Linkerd) for zero-trust networking
3. **RBAC**: Implement role-based access control for all services
4. **Audit Logging**: Enable and centralize audit logs for all authentication events
5. **Penetration Testing**: Regular security assessments

## Kubernetes Security (Future)

When migrating to Kubernetes, implement:
1. **NetworkPolicies**: Deny all traffic by default, allow only required connections
2. **Pod Security Standards**: Enforce restricted pod security policies
3. **Service Mesh**: Consider Istio or Linkerd for advanced traffic management
4. **Secrets Encryption**: Enable etcd encryption at rest
5. **RBAC**: Fine-grained Kubernetes RBAC policies

## Incident Response

In case of security incident:
1. **Isolate**: Use `docker network disconnect` to isolate compromised containers
2. **Audit**: Review Traefik access logs, application logs in Loki
3. **Rotate**: Immediately rotate all credentials
4. **Backup**: Restore from last known good backup if needed
5. **Update**: Patch vulnerabilities and redeploy

## Compliance Notes

- **GDPR**: Ensure PII in logs is masked or encrypted
- **PCI-DSS**: If processing payments, additional network segmentation required
- **HIPAA**: Healthcare data requires encryption in transit and at rest
- **SOC 2**: Maintain audit logs for all access (implemented via Loki + Prometheus)

## References

- Traefik Security Documentation: https://doc.traefik.io/traefik/https/overview/
- Docker Network Security: https://docs.docker.com/network/network-tutorial-standalone/
- OWASP Docker Security: https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html
