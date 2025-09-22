# 0) One-shot scaffolder (copy–paste and run)

> This creates `~/n8n-stack` and everything inside it. Safe to run from any directory.

```bash
# create an isolated n8n stack in ~/n8n-stack
mkdir -p ~/n8n-stack && cd ~/n8n-stack

# ----------------------------
# env file (edit values!)
# ----------------------------
cat > .env <<'EOF'
# === domain config (only needed if you enable Traefik) ===
DOMAIN_NAME=example.com
SUBDOMAIN=n8n
SSL_EMAIL=admin@example.com

# === required for n8n ===
GENERIC_TIMEZONE=Asia/Kolkata
TZ=Asia/Kolkata

# strong random key (change me): openssl rand -hex 48
N8N_ENCRYPTION_KEY=change-me-super-long-random

# create this in n8n UI (Settings → n8n API) after first login
N8N_API_KEY=put-your-x-n8n-api-key-here
EOF

# ----------------------------
# compose file (isolated project)
# ----------------------------
cat > compose.yaml <<'EOF'
name: n8n_stack

networks:
  edge: {}
  backplane:
    internal: true

volumes:
  n8n_data:
  traefik_data:

services:
  # optional HTTPS reverse proxy (binds :80/:443). Comment out if ports in use.
  traefik:
    image: traefik:latest
    restart: unless-stopped
    command:
      - --api.insecure=true
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --entrypoints.web.address=:80
      - --entrypoints.web.http.redirections.entryPoint.to=websecure
      - --entrypoints.web.http.redirections.entrypoint.scheme=https
      - --entrypoints.websecure.address=:443
      - --certificatesresolvers.mytlschallenge.acme.tlschallenge=true
      - --certificatesresolvers.mytlschallenge.acme.email=${SSL_EMAIL}
      - --certificatesresolvers.mytlschallenge.acme.storage=/letsencrypt/acme.json
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - traefik_data:/letsencrypt
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks: [edge, backplane]

  n8n:
    build:
      context: ./n8n
    image: local/n8n-with-logs:latest
    restart: unless-stopped
    depends_on: [traefik]
    # local development access even without Traefik
    ports:
      - "127.0.0.1:5678:5678"
    environment:
      - N8N_HOST=${SUBDOMAIN}.${DOMAIN_NAME}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://${SUBDOMAIN}.${DOMAIN_NAME}/
      - GENERIC_TIMEZONE=${GENERIC_TIMEZONE}
      - TZ=${TZ}
      - NODE_ENV=production
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}

      # runners + native python runner (optional beta)
      - N8N_RUNNERS_ENABLED=true
      - N8N_NATIVE_PYTHON_RUNNER=true

      # file logging
      - N8N_LOG_LEVEL=info
      - N8N_LOG_OUTPUT=file
      - N8N_LOG_FILE_LOCATION=/var/log/n8n/n8n.log
      - N8N_LOG_FILE_SIZE_MAX=32
      - N8N_LOG_FILE_COUNT_MAX=30

      # harden a bit
      - N8N_DIAGNOSTICS_ENABLED=false
      - N8N_VERSION_NOTIFICATIONS_ENABLED=false
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n/local-files:/files
      - ./n8n/logs:/var/log/n8n
      - ./n8n/custom-nodes:/home/node/.n8n/custom-nodes
    labels:
      - traefik.enable=true
      - traefik.http.routers.n8n.rule=Host(`${SUBDOMAIN}.${DOMAIN_NAME}`)
      - traefik.http.routers.n8n.entrypoints=web,websecure
      - traefik.http.routers.n8n.tls.certresolver=mytlschallenge
    networks: [edge, backplane]

  # small proxy API so your other apps can trigger n8n webhooks and query executions
  automation-api:
    build:
      context: ./automation-api
    image: local/automation-api:latest
    restart: unless-stopped
    depends_on: [n8n]
    environment:
      - PORT=8080
      - N8N_BASE_URL=http://n8n:5678
      - N8N_API_KEY=${N8N_API_KEY}
    ports:
      - "127.0.0.1:8080:8080"
    labels:
      - traefik.enable=true
      - traefik.http.routers.automation-api.rule=Host(`api.${DOMAIN_NAME}`)
      - traefik.http.routers.automation-api.entrypoints=web,websecure
      - traefik.http.routers.automation-api.tls.certresolver=mytlschallenge
    networks: [edge, backplane]
EOF

# ----------------------------
# n8n Dockerfile + dirs
# ----------------------------
mkdir -p n8n/{local-files,logs,custom-nodes}
cat > n8n/Dockerfile <<'EOF'
FROM docker.n8n.io/n8nio/n8n:1.111.0

USER root
RUN mkdir -p /var/log/n8n /files && \
    chown -R node:node /var/log/n8n /files /home/node/.n8n
USER node

# sensible logging defaults (override via env)
ENV N8N_LOG_OUTPUT=file \
    N8N_LOG_LEVEL=info \
    N8N_LOG_FILE_LOCATION=/var/log/n8n/n8n.log \
    N8N_LOG_FILE_SIZE_MAX=32 \
    N8N_LOG_FILE_COUNT_MAX=30
EOF

# ----------------------------
# automation-api (FastAPI)
# ----------------------------
mkdir -p automation-api
cat > automation-api/requirements.txt <<'EOF'
fastapi
uvicorn
httpx
EOF

cat > automation-api/Dockerfile <<'EOF'
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN adduser --disabled-password --gecos '' app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
USER app
ENV PORT=8080
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

cat > automation-api/main.py <<'EOF'
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx, os

app = FastAPI(title="Automation API", version="1.0.0")
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://n8n:5678")
N8N_API_KEY  = os.getenv("N8N_API_KEY", "")

def api_headers():
    if not N8N_API_KEY:
        raise RuntimeError("N8N_API_KEY not set")
    return {"X-N8N-API-KEY": N8N_API_KEY}

@app.get("/healthz")
async def health():
    return {"ok": True}

@app.get("/n8n/executions")
async def list_executions(limit: int = 20, lastId: int | None = None):
    params = {"limit": limit}
    if lastId is not None:
        params["lastId"] = lastId
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{N8N_BASE_URL}/api/v1/executions",
                             headers=api_headers(), params=params)
        if r.status_code >= 400:
            raise HTTPException(r.status_code, r.text)
        return JSONResponse(r.json())

@app.post("/n8n/trigger/{webhook_path:path}")
async def trigger(webhook_path: str, request: Request):
    body = await request.body()
    headers = {"content-type": request.headers.get("content-type", "application/json")}
    url = f"{N8N_BASE_URL}/webhook/{webhook_path}".rstrip("/")
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, content=body, headers=headers)
        return JSONResponse(status_code=r.status_code, content=r.text)
EOF

# ----------------------------
# helpful .gitignore
# ----------------------------
cat > .gitignore <<'EOF'
# n8n isolated stack
n8n/logs
n8n/local-files
.env
EOF

# done
echo "Scaffolded to $(pwd)"
```

---

# 1) Resulting folder structure

```text
~/n8n-stack
├── .env                 # your secrets + domain vars
├── .gitignore
├── compose.yaml         # completely isolated compose project
├── automation-api/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
└── n8n/
    ├── Dockerfile       # n8n image with file logging
    ├── custom-nodes/
    ├── local-files/
    └── logs/
```

---

# 2) Bring it up (isolated)

> If you haven’t, add your user to docker group once:
> `sudo usermod -aG docker "$USER" && exec sg docker newgrp`

```bash
cd ~/n8n-stack

# sanity check compose + env
docker compose --env-file ./.env config

# build & start (ports 80/443 must be free if Traefik is enabled)
docker compose up -d --build

# see containers
docker compose ps

# initial logs
docker compose logs -f n8n
```

* open n8n locally: **[http://127.0.0.1:5678](http://127.0.0.1:5678)** (first-time setup)
* after you set up, create an **API key** in n8n UI (Settings → n8n API), then put it into `.env` and `docker compose up -d` again.

---

# 3) Cross-checks (verify “everything properly”)

**basic health**

```bash
# check docker sees the project
docker compose ls | grep n8n_stack

# services healthy?
docker compose ps

# ports bound (local only)
ss -lntp | grep -E '(:5678|:8080|:80 |:443 )'
```

**n8n reachable**

```bash
# head request (should return 200/302)
curl -I http://127.0.0.1:5678

# file logs written?
ls -lah n8n/logs
tail -n 50 n8n/logs/n8n.log
```

**automation API reachable**

```bash
curl http://127.0.0.1:8080/healthz
# (after you set N8N_API_KEY)
curl "http://127.0.0.1:8080/n8n/executions?limit=5"
```

**networks & volumes isolated**

```bash
docker network ls | grep n8n_stack
docker network inspect n8n_stack_edge -f '{{.Name}} has {{len .Containers}} containers'
docker volume inspect n8n_stack_n8n_data >/dev/null && echo "n8n_data OK"
```

**optional HTTPS checks (if DNS is set to your server and Traefik is enabled)**

```bash
# replace with your real domain/subdomain
dig +short n8n.${DOMAIN_NAME}
curl -I https://n8n.${DOMAIN_NAME}
```

---

# 4) How to use the **automation API** (optional)

* create a workflow in n8n that starts with a **Webhook** node at path `ingest/orders`
* then:

```bash
# trigger via the proxy API (for clean auth-less public endpoint on your side)
curl -X POST http://127.0.0.1:8080/n8n/trigger/ingest/orders \
  -H 'content-type: application/json' \
  -d '{"order_id":123,"total":999}'
```

* list last executions (the proxy adds `X-N8N-API-KEY`):

```bash
curl "http://127.0.0.1:8080/n8n/executions?limit=10"
```

---

# 5) Start/Stop/Update

```bash
# stop
docker compose stop

# start after stop
docker compose start

# rebuild after edits
docker compose build --no-cache n8n automation-api && docker compose up -d

# full down (keeps volumes)
docker compose down

# nuke everything (including data!)
docker compose down -v
```

---
