# Requirements — LLMObs Frontend Deployment

System prerequisites, dependencies, and configuration requirements for running the LLMObs Frontend Deployment infrastructure stack on any machine.

---

## System Requirements

### Hardware (Minimum)

| Resource | Minimum | Recommended |
| :--- | :--- | :--- |
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8+ GB |
| **Disk** | 10 GB free | 20+ GB free |
| **Network** | Local network access | Ports 31410–31419 free |

### Operating System

| OS | Supported | Notes |
| :--- | :--- | :--- |
| **Ubuntu 20.04+** | ✅ Primary | Tested and recommended |
| **Debian 11+** | ✅ | Works out of the box |
| **macOS 12+** | ✅ | Docker Desktop required |
| **Windows 10/11** | ✅ | WSL2 + Docker Desktop required |
| **RHEL/CentOS 8+** | ✅ | Use `dnf` instead of `apt` |

---

## Software Dependencies

### Required (Blocking — Setup Will Fail Without These)

| Dependency | Minimum Version | Install Command (Ubuntu/Debian) | Purpose |
| :--- | :--- | :--- | :--- |
| **Docker Engine** | `20.10+` | [docs.docker.com/install](https://docs.docker.com/engine/install/) | Container runtime |
| **Docker Compose** | `2.0+` (plugin) | `sudo apt install docker-compose-plugin` | Multi-container orchestration |
| **OpenSSL** | `1.1.1+` | `sudo apt install openssl` | TLS certificate generation |
| **Node.js** | `18.0+` | [nodejs.org](https://nodejs.org/en/download/) | npm scripts, TypeScript tests |
| **npm** | `9.0+` | Bundled with Node.js | Package manager |
| **curl** | Any | `sudo apt install curl` | HTTP endpoint health checks |
| **netcat (nc)** | Any | `sudo apt install netcat-openbsd` | TCP port health checks |
| **bash** | `4.0+` | Pre-installed on Linux/macOS | Shell scripts |

### Optional (Non-Blocking — Enhance Functionality)

| Dependency | Install Command | Purpose |
| :--- | :--- | :--- |
| **fuser** | `sudo apt install psmisc` | Auto-kill processes on occupied ports |
| **lsof** | `sudo apt install lsof` | Fallback port-process detection |
| **jq** | `sudo apt install jq` | JSON parsing in scripts |

---

## Port Allocation

All ports are in the `31410–31419` range to avoid conflicts with standard services.

| Port | Protocol | Service | Exposed To |
| :--- | :--- | :--- | :--- |
| `31410` | HTTP | Traefik Gateway (HTTP → HTTPS redirect) | Host |
| `31411` | HTTP | Traefik Admin Dashboard | Host |
| `31413` | TCP | Redis Cache (auth required) | Host |
| `31414` | TCP | Kafka Broker | Internal network only |
| `31415` | HTTP | Grafana UI | Host |
| `31416` | HTTP | Grafana Tempo API | Host |
| `31417` | HTTP | OTel Collector OTLP HTTP | Host |
| `31418` | gRPC | OTel Collector OTLP gRPC | Host |
| `31419` | HTTPS | Traefik Gateway (TLS termination) | Host |

> **Important**: Ensure ports `31410–31419` are not in use by other services. Run `npm run free-ports` to auto-clear them.

---

## Network Requirements

### DNS / Hosts Configuration

The following custom domains must resolve to `127.0.0.1`. Add to `/etc/hosts`:

```
127.0.0.1  llmobs.gateway llmobs.grafana llmobs.tempo llmobs.otel llmobs.kafka llmobs.redis
```

### Firewall Rules

If a local firewall is active, allow TCP on ports `31410–31419`:

```bash
# UFW (Ubuntu)
sudo ufw allow 31410:31419/tcp

# firewalld (RHEL/CentOS)
sudo firewall-cmd --add-port=31410-31419/tcp --permanent && sudo firewall-cmd --reload

# iptables
sudo iptables -A INPUT -p tcp --dport 31410:31419 -j ACCEPT
```

---

## TLS / Certificate Requirements

### Auto-Generated (Default)

The setup script (`scripts/setup.sh`) generates self-signed certificates automatically using OpenSSL. No manual certificate configuration is needed for local development.

**Generated files** (stored in `config/certs/`):

| File | Purpose |
| :--- | :--- |
| `ca.pem` | Root CA certificate |
| `ca-key.pem` | Root CA private key (600 permissions) |
| `server.pem` | Server certificate with SAN entries |
| `server-key.pem` | Server private key (600 permissions) |
| `openssl-san.cnf` | OpenSSL config with Subject Alternative Names |

**SAN (Subject Alternative Name) entries** included in the server certificate:
- `llmobs.gateway`, `llmobs.grafana`, `llmobs.tempo`, `llmobs.otel`, `llmobs.kafka`, `llmobs.redis`
- `gateway.llmobs.local`, `grafana.llmobs.local`, `tempo.llmobs.local`, `otel.llmobs.local`
- `localhost`, `127.0.0.1`, `::1`

### Production Certificates

For production deployments, replace the self-signed certificates with real ones:

1. Place your CA cert, server cert, and server key in `config/certs/`
2. Update the paths in `.env` if filenames differ
3. Or use Let's Encrypt with Traefik's built-in ACME resolver

---

## Security Configuration

### Request-Level Security (Traefik Middlewares)

All request-level security is centrally configured in `config/traefik/dynamic.yml`:

| Protection | Configuration | Default |
| :--- | :--- | :--- |
| **Rate Limiting** | Requests per second per client IP | 100 req/s average, 200 burst |
| **Payload Size Limit** | Maximum request body size | 10 MB |
| **Security Headers** | HSTS, X-Frame-Options, XSS protection | Enabled on all routes |
| **IP Allowlisting** | Optional source IP filtering | Disabled (all allowed) |
| **Circuit Breaker** | Auto-disable unhealthy backends | 50% error threshold |

### Service-Level Security

| Service | Authentication | Encryption | Network |
| :--- | :--- | :--- | :--- |
| **Redis** | `requirepass` (password from `.env`) | In-transit (internal network) | Isolated bridge network |
| **Kafka** | None (internal only) | In-transit (internal network) | Not exposed to host |
| **Grafana** | Admin user/password from `.env` | TLS via Traefik gateway | Sign-up disabled |
| **Tempo** | None (internal only) | In-transit (internal network) | Isolated bridge network |
| **OTel Collector** | None (ingestion endpoint) | In-transit (internal network) | Isolated bridge network |
| **Traefik** | Dashboard (insecure mode for local dev) | TLS termination | Gateway — all traffic routed through |

### Docker Security Hardening

| Measure | Applied To | Description |
| :--- | :--- | :--- |
| `security_opt: no-new-privileges` | All containers | Prevent privilege escalation |
| `read_only: true` | Stateless containers | Read-only root filesystem |
| `tmpfs` mounts | Containers needing `/tmp` | Ephemeral writable directories |
| Bridge network isolation | All containers | `llmobs-network` — not using host network |
| Minimal port exposure | Internal services | Only gateway ports exposed to host |

---

## Environment Variables

All secrets and configuration values are defined in `.env` (single source of truth):

| Variable | Description | Default |
| :--- | :--- | :--- |
| `LLMOBS_DOMAIN` | Base domain for custom URLs | `llmobs.local` |
| `REDIS_PASSWORD` | Redis authentication password | Auto-generated by setup |
| `GF_SECURITY_ADMIN_USER` | Grafana admin username | `admin` |
| `GF_SECURITY_ADMIN_PASSWORD` | Grafana admin password | Auto-generated by setup |
| `KAFKA_CLUSTER_ID` | Kafka cluster identifier | `llmobs-kafka-cluster-001` |
| `TLS_CERT_DIR` | Directory containing TLS certs | `./config/certs` |
| `TLS_CERT_FILE` | Server certificate path | `./config/certs/server.pem` |
| `TLS_KEY_FILE` | Server private key path | `./config/certs/server-key.pem` |
| `TLS_CA_FILE` | CA certificate path | `./config/certs/ca.pem` |
| `PORT_TRAEFIK_HTTP` | Traefik HTTP port | `31410` |
| `PORT_TRAEFIK_HTTPS` | Traefik HTTPS port | `31419` |
| `PORT_TRAEFIK_DASHBOARD` | Traefik dashboard port | `31411` |
| `PORT_REDIS` | Redis port | `31413` |
| `PORT_KAFKA` | Kafka port | `31414` |
| `PORT_GRAFANA` | Grafana port | `31415` |
| `PORT_TEMPO` | Tempo port | `31416` |
| `PORT_OTEL_HTTP` | OTel Collector HTTP port | `31417` |
| `PORT_OTEL_GRPC` | OTel Collector gRPC port | `31418` |

---

## Quick Start (Fresh Machine)

```bash
# 1. Navigate to the package
cd packages/node/frontend-deployment

# 2. Run the full setup (checks prereqs, generates certs, configures hosts, pulls images)
./scripts/setup.sh

# 3. Start the stack
npm run up

# 4. Verify everything is working
npm run health

# 5. Run integration tests
npm run test
```

---

## Troubleshooting

| Issue | Solution |
| :--- | :--- |
| Port already in use | Run `npm run free-ports` to auto-kill processes |
| Docker permission denied | Add user to docker group: `sudo usermod -aG docker $USER` |
| Certificate expired | Regenerate: `npm run certs -- --force` |
| /etc/hosts not configured | Run `npm run setup` or add manually |
| Container keeps restarting | Check logs: `npm run logs -- <service-name>` |
| Redis auth failure | Verify `REDIS_PASSWORD` in `.env` matches client config |
