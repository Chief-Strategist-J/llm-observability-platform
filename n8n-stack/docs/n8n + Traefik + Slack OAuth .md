# n8n + Traefik + Slack OAuth (Local HTTPS) — Technical Runbook

## 0) Scope & Assumptions

* Your compose file is the one you posted; we’ll **only add minimal pieces** (TLS file provider for Traefik, two volume mounts, one dynamic file, three n8n labels for HTTPS, 2 env changes).
* Hostnames use `n8n.localtest.me` (resolves to 127.0.0.1 with wildcard DNS). No `/etc/hosts` edits needed. ([The Official Microsoft ASP.NET Site][2])
* You’ll generate a locally-trusted cert with **mkcert** (simple, no OpenSSL wrangling). ([GitHub][3])

---

## 1) Topology (at a glance)

```
Browser ──HTTPS──▶ Traefik (:8443 or :443) ──HTTP──▶ n8n (:5678)
                    │
                    └── dynamic TLS (file provider) → mkcert certs

Slack OAuth flow:
Slack → (redirect to) https://n8n.localtest.me[:443]/rest/oauth2-credential/callback
        └── must be HTTPS (Slack requirement)
```

* n8n builds webhook & OAuth URLs from `WEBHOOK_URL` (and protocol/host/port), so we must **point it at HTTPS** behind Traefik. ([n8n Docs][4])
* The **OAuth2 callback path** in n8n is `/rest/oauth2-credential/callback`. ([n8n Community][5])

---

## 2) Prerequisites

* **mkcert** installed and root CA added to your trust store (one-time): `mkcert -install`. ([GitHub][3])
* Traefik will read certs via a **dynamic file provider** (recommended way). ([Traefik Labs Documentation][6])

---

## 3) Prepare local TLS

Create folders and a dynamic TLS file:

```bash
mkdir -p traefik/certs traefik/dynamic

# Create a cert for your dev hostname
mkcert -key-file traefik/certs/n8n.localtest.me-key.pem \
       -cert-file traefik/certs/n8n.localtest.me.pem \
       n8n.localtest.me

# Tell Traefik where to find the cert
cat > traefik/dynamic/tls.yml <<'YAML'
tls:
  certificates:
    - certFile: /certs/n8n.localtest.me.pem
      keyFile: /certs/n8n.localtest.me-key.pem
YAML
```

---

## 4) Minimal compose patch (what & why)

> **Principle:** keep your HTTP route intact; just **add** an HTTPS route and make n8n **advertise HTTPS** so the Slack redirect is HTTPS.

### 4.1 Traefik: enable file provider + mount certs/dynamic config

Add two command flags and two volume mounts to `traefik`:

```diff
 services:
   traefik:
     image: traefik:latest
     command:
       - --api.insecure=true
       - --providers.docker=true
       - --providers.docker.exposedbydefault=false
       - --entrypoints.web.address=:8081
       - --entrypoints.websecure.address=:8443
       - --log.level=INFO
       - --accesslog=true
+      - --providers.file.directory=/dynamic
+      - --providers.file.watch=true
     ports:
       - "127.0.0.1:8081:8081"
       - "127.0.0.1:8443:8443"
     volumes:
       - /var/run/docker.sock:/var/run/docker.sock:ro
+      - ./traefik/dynamic:/dynamic:ro
+      - ./traefik/certs:/certs:ro
```

**Why:** Load the dynamic TLS file with your mkcert cert/key. ([Traefik Labs Documentation][6])

### 4.2 n8n: add HTTPS router labels (keep your current HTTP router)

Add three labels under `n8n.labels`:

```diff
   n8n:
     labels:
       - traefik.enable=true
       - traefik.http.routers.n8n.rule=Host(`n8n.localtest.me`)
       - traefik.http.routers.n8n.entrypoints=web
       - traefik.http.services.n8n.loadbalancer.server.port=5678
+      - traefik.http.routers.n8n-https.rule=Host(`n8n.localtest.me`)
+      - traefik.http.routers.n8n-https.entrypoints=websecure
+      - traefik.http.routers.n8n-https.tls=true
```

**Why:** Create an HTTPS route on Traefik’s `websecure` entrypoint using your cert. ([Traefik Labs Documentation][7])

### 4.3 n8n: advertise HTTPS (so OAuth redirect is HTTPS)

Change two env vars (and consider a third):

```diff
   n8n:
     environment:
-      - N8N_PROTOCOL=http
-      - WEBHOOK_URL=http://n8n.localtest.me:8081/
+      - N8N_PROTOCOL=https
+      - WEBHOOK_URL=https://n8n.localtest.me:8443/
+      - N8N_PROXY_HOPS=1
```

**Why:** n8n generates & displays webhook/OAuth URLs based on these; behind a reverse proxy you must set `WEBHOOK_URL` explicitly. `N8N_PROXY_HOPS=1` helps n8n respect `X-Forwarded-*` from Traefik. ([n8n Docs][4])

> Optional (good once HTTPS is working):
> `N8N_SECURE_COOKIE=true` so cookies are marked Secure.

**Restart:**

```bash
docker compose up -d --build traefik n8n
```

---

## 5) Configure Slack App (OAuth & Permissions)

1. In your Slack app → **OAuth & Permissions → Redirect URLs**, add:

```
https://n8n.localtest.me:8443/rest/oauth2-credential/callback
```

> Slack explicitly requires **HTTPS** redirect URLs (whether set in the URL or in the App config). ([Slack Developer Docs][1])

2. Add scopes you need, then **Install to Workspace**.

> If a tool is picky about ports, you can map Traefik to host **:443** instead:
>
> * Change Traefik ports: `127.0.0.1:443:8443`
> * Set `WEBHOOK_URL=https://n8n.localtest.me/`
>
> Then register `https://n8n.localtest.me/rest/oauth2-credential/callback` in Slack. (HTTPS is the requirement; port 443 keeps URLs simple.) ([Slack Developer Docs][1])

---

## 6) Connect n8n → Slack (Credential)

* In n8n Credentials, create **Slack OAuth2** (or HTTP Request OAuth2) with your Slack Client ID/Secret → **Connect**.
* n8n will open an HTTPS window and **show the same HTTPS redirect** you registered.
* After approval, n8n stores tokens for the credential.

> FYI: n8n’s OAuth2 callback endpoint is `/rest/oauth2-credential/callback`. ([n8n Community][5])

---

## 7) Validation Checklist (quick & dirty)

* **Browser:** open `https://n8n.localtest.me:8443/` → no cert warning (mkcert’s CA is trusted). ([GitHub][3])
* **curl:**

  ```bash
  curl -I https://n8n.localtest.me:8443/
  ```

  Expect `HTTP/1.1 200` via Traefik (or 302 to `/workflow`, depending on version).
* **Traefik access log:** see TLS handshake and GET to `websecure` entrypoint. ([Traefik Labs Documentation][7])
* **n8n credential:** “Connect” completes, no “HTTPS required” or `redirect_uri_mismatch`.

---

## 8) Troubleshooting Matrix

| Symptom                                         | Likely cause                                                                                                         | Quick fix                                                                                                                                                                                                                                       |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Slack says “HTTPS required”**                 | Redirect URL isn’t HTTPS or n8n is advertising HTTP                                                                  | Ensure `N8N_PROTOCOL=https` and `WEBHOOK_URL` starts with `https://`. Verify Slack’s Redirect URLs entry uses `https://.../rest/oauth2-credential/callback`. ([Slack Developer Docs][1])                                                        |
| **`redirect_uri_mismatch`**                     | Slack’s Redirect URL **does not exactly match** what n8n used (host, scheme, port, path, trailing slash)             | Use *one* public URL in both places. If you mapped host 443→Traefik 8443, remove `:8443` from `WEBHOOK_URL` and from Slack config. Keep `/rest/oauth2-credential/callback` exact. ([Slack Developer Docs][1])                                   |
| **Browser shows cert warning**                  | mkcert CA not installed/trusted                                                                                      | Run `mkcert -install` again; restart browser. ([GitHub][3])                                                                                                                                                                                     |
| **Traefik serves HTTP but not HTTPS**           | Dynamic TLS not loaded or cert path not mounted                                                                      | Check Traefik flags `--providers.file.directory=/dynamic`, mount `./traefik/dynamic:/dynamic:ro`, `./traefik/certs:/certs:ro`, and confirm `tls.yml` file exists. ([Traefik Labs Documentation][6])                                             |
| **OAuth loop → `invalid_state`**                | Cookie not sent (mixing http/https domains/tabs), or multiple base URLs                                              | Stick to **one** hostname & scheme. Set `N8N_SECURE_COOKIE=true` once HTTPS is stable; retry in a fresh window. ([n8n Docs][4])                                                                                                                 |
| **`ECONNREFUSED 127.0.0.1:8081` inside a node** | A node tries to hit `http://127.0.0.1:8081` (Traefik) from **inside a container** (127.0.0.1 = the container itself) | Inside containers, call other services by **Docker DNS name** (e.g., `http://n8n:5678`), or call via the routed hostname but publish the port to the host correctly. Your `automation-api` already targets `http://n8n:5678` — keep doing that. |
| **`EAI_AGAIN` DNS errors**                      | Resolver hiccup in container                                                                                         | You already set `dns:` in `n8n`. If it persists, check `/etc/resolv.conf` inside the container, reduce `dns_opt` timeouts a bit, or try a single well-known resolver.                                                                           |

---

## 9) ASCII Decision Tree (when OAuth fails)

```
Start
 |
 |-- Can you open https://n8n.localtest.me[:443|8443]/ without cert warning?
 |       |-- No -> Fix mkcert/trust & Traefik dynamic TLS (Step 3-4)
 |       `-- Yes
 |
 |-- Does Slack Redirect URL EXACTLY match your public n8n URL + /rest/oauth2-credential/callback?
 |       |-- No -> Fix Slack app Redirect URLs & n8n WEBHOOK_URL (Step 5, 4.3)
 |       `-- Yes
 |
 |-- Is WEBHOOK_URL set to the same https:// host[:port]/ you configured?
 |       |-- No -> Set & restart (Step 4.3)
 |       `-- Yes
 |
 `-- Still failing?
         |-- invalid_state -> One hostname only; clear cookies; set SECURE cookie once on HTTPS
         |-- mismatch -> Double-check scheme/port/path/trailing slash
         `-- container can't reach -> use Docker DNS (service name:port), not 127.0.0.1
```

---

## 10) Optional: Use :443 for cleaner URLs

If you prefer no port in the public URL:

```diff
traefik:
  ports:
-   - "127.0.0.1:8443:8443"
+   - "127.0.0.1:443:8443"

n8n.environment:
-  - WEBHOOK_URL=https://n8n.localtest.me:8443/
+  - WEBHOOK_URL=https://n8n.localtest.me/
```

Then register `https://n8n.localtest.me/rest/oauth2-credential/callback` in Slack. ([Slack Developer Docs][1])

---

## 11) Rollback Plan

* Remove the two Traefik file-provider flags and the two volume mounts.
* Remove the three `n8n-https` labels.
* Restore `N8N_PROTOCOL=http` and `WEBHOOK_URL=http://n8n.localtest.me:8081/`.
* `docker compose up -d traefik n8n`.

---

## 12) Security Notes (local dev)

* **mkcert** creates a local CA and installs it to your system trust; it’s intended for dev. Don’t ship these certs to prod. ([GitHub][3])
* Your compose binds Traefik ports to **127.0.0.1**, so services aren’t exposed externally (good).

---

## 13) Reference Links

* **Slack OAuth**: HTTPS is mandatory for Redirect URLs. ([Slack Developer Docs][1])
* **n8n behind reverse proxy**: set `WEBHOOK_URL` and proxy headers. ([n8n Docs][4])
* **n8n OAuth2 callback path**: `/rest/oauth2-credential/callback`. ([n8n Community][5])
* **Traefik TLS & file provider**: dynamic TLS configuration. ([Traefik Labs Documentation][7])
* **mkcert**: locally-trusted certs. ([GitHub][3])
* **localtest.me**: wildcard DNS → 127.0.0.1. ([The Official Microsoft ASP.NET Site][2])

---
