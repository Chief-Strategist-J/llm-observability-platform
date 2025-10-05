# Loki ↔ Grafana in Docker — Troubleshooting Playbook (Problem → Solution)

**Headline:** *“No more blind dashboards: fix Loki–Grafana in minutes with clean problem–solution steps.”*

**Opening:**
When Grafana can’t talk to Loki, you lose visibility exactly when you need it. Almost every failure boils down to five areas: **networks, ports, names (DNS), config, and permissions**. Use the map below to jump to your exact problem, then follow the fix checklist.

---

## Quick Map (Problems → Solutions)

| # | Problem                                | Symptom (what you see)                                 | Go to                                                 |
| - | -------------------------------------- | ------------------------------------------------------ | ----------------------------------------------------- |
| 1 | Grafana not reachable from your laptop | Browser can’t open `http://127.0.0.1:3030`             | [Fix #1](#fix-1-grafana-not-reachable-from-host)      |
| 2 | Grafana can’t resolve or reach Loki    | Datasource fails; `getent hosts loki` fails            | [Fix #2](#fix-2-grafana-cant-resolve-or-reach-loki)   |
| 3 | Loki config parse errors               | Loki crash loop with YAML/unmarshal errors             | [Fix #3](#fix-3-loki-configuration-parse-errors)      |
| 4 | Loki permission/WAL errors             | “permission denied”, WAL can’t be created              | [Fix #4](#fix-4-loki-permission-and-wal-errors)       |
| 5 | Datasource URL wrong                   | Using `localhost` inside Grafana; datasource unhealthy | [Fix #5](#fix-5-grafana-datasource-url-misconfigured) |

---

## Fix #1: Grafana not reachable from host

**Problem**
Grafana is running but your browser can’t open `http://127.0.0.1:3030`.

**Symptoms**

* `curl -I http://127.0.0.1:3030` → connection refused / not found
* `docker port n8n_stack-grafana-1` → no mapping for 3030

**Diagnosis (commands)**

```bash
docker ps --format 'table {{.Names}}\t{{.Ports}}' | grep grafana
docker port n8n_stack-grafana-1
```

**Solution (Compose snippet)**

```yaml
networks:
  edge: {}
  backplane:
    internal: true

grafana:
  image: grafana/grafana:10.4.6
  restart: unless-stopped
  environment:
    - GF_SERVER_HTTP_ADDR=0.0.0.0
    - GF_SERVER_HTTP_PORT=3030
  ports:
    - "127.0.0.1:3030:3030"     # publish to host
  networks:
    - backplane                 # talk to Loki
    - edge                      # reachable from host
  volumes:
    - grafana_data:/var/lib/grafana
    - ./grafana/grafana.ini:/etc/grafana/grafana.ini:ro
    - ./grafana/provisioning:/etc/grafana/provisioning:ro
```

**Verify**

```bash
docker port n8n_stack-grafana-1 | grep 3030     # shows 127.0.0.1:3030
curl -sI http://127.0.0.1:3030 | head -n1       # HTTP/200
```

**Prevent**

* Keep Grafana on **both** `edge` and `backplane`.
* Publish **only** Grafana’s port to host; keep internal services private.

---

## Fix #2: Grafana can’t resolve or reach Loki

**Problem**
Grafana can’t reach `loki` by name; datasource errors or alerts fail.

**Symptoms**

* Inside Grafana: `getent hosts loki` fails
* Grafana logs show connection/DNS errors to `loki:3100`

**Diagnosis (commands)**

```bash
# Are both containers on the same user-defined network?
docker inspect n8n_stack-grafana-1 --format '{{json .NetworkSettings.Networks}}' | jq .
docker inspect n8n_stack-loki-1    --format '{{json .NetworkSettings.Networks}}' | jq .

# DNS test inside Grafana
docker exec -it n8n_stack-grafana-1 getent hosts loki
```

**Solution (Compose snippet)**

> Containers must share at least one **user-defined** network. Using `internal: true` is fine; it only blocks host access, not container-to-container comms.

```yaml
networks:
  edge: {}
  backplane:
    internal: true

loki:
  image: grafana/loki:2.9.8
  networks:
    backplane:
      aliases: [loki]   # optional; default name usually enough

grafana:
  networks:
    - backplane
    - edge
```

**Verify**

```bash
docker exec -it n8n_stack-grafana-1 getent hosts loki  # shows an IP
```

**Prevent**

* Always put Grafana and Loki on the **same** user-defined network (e.g., `backplane`).
* Avoid default/legacy bridge assumptions; explicitly declare networks in Compose.

---

## Fix #3: Loki configuration parse errors

**Problem**
Loki keeps restarting with YAML/unmarshal errors or wrong keys.

**Symptoms**

* Errors like: `yaml: unmarshal errors:` or
  `field path not found in type common.Config`

**Diagnosis (commands)**

```bash
docker logs n8n_stack-loki-1 --tail=50
# Optional offline validation:
docker run --rm -v $PWD/loki/config.yml:/etc/loki/config.yml grafana/loki:2.9.8 \
  -config.file=/etc/loki/config.yml -verify-config
```

**Solution (working Loki 2.9.x config)**

```yaml
# ./loki/config.yml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /var/loki
  storage:
    filesystem:
      chunks_directory: /var/loki/chunks
      rules_directory:  /var/loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

query_range:
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 100

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
```

**Verify**

```bash
docker logs n8n_stack-loki-1 --tail=50 | grep -i "ready" -n || true
```

**Prevent**

* Match config keys to your **Loki version** (e.g., `common.path_prefix` for 2.9.x).
* Keep a validation command in CI to catch YAML/schema issues before deploy.

---

## Fix #4: Loki permission and WAL errors

**Problem**
Loki can’t write its WAL or data, causing crash loops.

**Symptoms**

* `creating WAL folder ... permission denied`
* `mkdir /var/loki: permission denied`

**Diagnosis (commands)**

```bash
docker inspect n8n_stack-loki-1 --format '{{json .Mounts}}' | jq .
# Check ownership/permissions of your host directory if bind-mounting.
```

**Solution (choose one)**

**A) Quick unblock (less strict): run as root**

```yaml
loki:
  image: grafana/loki:2.9.8
  user: root
  volumes:
    - ./loki/config.yml:/etc/loki/config.yml:ro
    - loki_data:/var/loki
  networks: [backplane]
```

**B) Safer (recommended): fix ownership to Loki’s UID/GID**

1. Find Loki UID/GID (commonly `10001:10001`).
2. Chown your data directory on host (if bind-mounting), or rely on a named volume.

**Verify**

```bash
docker logs n8n_stack-loki-1 --tail=50 | grep -Ei "ready|listening" -n || true
```

**Prevent**

* Always mount a **writable** directory for `/var/loki`.
* Prefer **named volumes** for portability and fewer host-permission surprises.

---

## Fix #5: Grafana datasource URL misconfigured

**Problem**
Datasource uses `http://127.0.0.1:3100` inside the Grafana container.

**Symptoms**

* Datasource health check fails
* Queries to Loki time out or refuse connection

**Diagnosis (commands)**

```bash
# List datasources
curl -s http://127.0.0.1:3030/api/datasources | jq '.'
```

**Solution (use service name over shared network)**

```yaml
# ./grafana/provisioning/datasources/loki.yaml
apiVersion: 1
datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100     # NOT localhost
    isDefault: true
    jsonData:
      maxLines: 1000
```

**Verify**

* Grafana → Connections → Data sources → Loki → “Save & test” shows **OK**.

**Prevent**

* Remember: inside containers, `localhost` means **the same container**.
* Use the **service name** (`loki`) on the **shared** network.

---

## Full Reference: Compose blocks and volumes

```yaml
networks:
  edge: {}
  backplane:
    internal: true

volumes:
  grafana_data:
  loki_data:

services:
  loki:
    image: grafana/loki:2.9.8
    restart: unless-stopped
    command: -config.file=/etc/loki/config.yml
    # user: root            # enable if host perms are tricky
    volumes:
      - ./loki/config.yml:/etc/loki/config.yml:ro
      - loki_data:/var/loki
    networks:
      - backplane

  grafana:
    image: grafana/grafana:10.4.6
    restart: unless-stopped
    environment:
      - GF_SERVER_HTTP_ADDR=0.0.0.0
      - GF_SERVER_HTTP_PORT=3030
      - GF_PATHS_CONFIG=/etc/grafana/grafana.ini
    ports:
      - "127.0.0.1:3030:3030"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/grafana.ini:/etc/grafana/grafana.ini:ro
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    networks:
      - backplane
      - edge
```

---

## Quick Health Checklist (copy–run)

```bash
# Containers up and ports
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E '(grafana|loki)'

# Host reachability
curl -sI http://127.0.0.1:3030 | head -n1

# Shared network?
docker inspect n8n_stack-grafana-1 --format '{{json .NetworkSettings.Networks}}' | jq .
docker inspect n8n_stack-loki-1    --format '{{json .NetworkSettings.Networks}}' | jq .

# DNS from inside Grafana
docker exec -it n8n_stack-grafana-1 getent hosts loki

# Loki readiness (only if port published)
curl -s http://127.0.0.1:3100/ready || echo "Loki not published—this is fine if Grafana uses backplane"
```

---

## Closing Takeaway

If you’re stuck, always walk the same five checks in order:
**(1) Grafana port published to host → (2) shared network with Loki → (3) datasource uses `http://loki:3100` → (4) Loki config valid for your version → (5) Loki data dir writable.**
This sequence resolves the vast majority of Loki–Grafana incidents fast and safely.
