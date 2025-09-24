# n8n Local Troubleshooting Runbook

**Stack (unchanged):** Traefik on **127.0.0.1:8081** (web) and **127.0.0.1:8443** (websecure), n8n on **:5678** (HTTP), automation-api, Grafana, Loki, Promtail.
**Focus:** fix **“route not found”** on 8081/8443 and **Google OAuth** errors; keep your compose exactly as-is.

---

## 1) What “route not found” means (and why you see it)

Traefik matches requests using **entrypoints** (ports) + **router rules** (like `Host(...)`).
In your compose, the n8n router is:

* **EntryPoint:** `web` → **:8081**
* **Rule:** `Host(\`n8n.localtest.me\`)\`
* **Upstream service port:** `5678`

So a request must:

1. arrive on **8081**, and
2. have **Host: n8n.localtest.me** in the HTTP request.

If either is missing, Traefik returns **404 Route not found**.

### Common cases that trigger 404

* Opening **[http://127.0.0.1:8081](http://127.0.0.1:8081)** (Host is `127.0.0.1`, not `n8n.localtest.me`).
* Opening **[https://n8n.localtest.me:8443](https://n8n.localtest.me:8443)** (your n8n router only listens on `web`/8081, not `websecure`/8443).
* Typos in the host (e.g., `n8n.localtestme`).

### The **one correct** n8n URL for your current compose

```
http://n8n.localtest.me:8081/
```

*(localtest.me always resolves to 127.0.0.1, so no /etc/hosts edits are needed.)*

### Quick proofs

```bash
# 1) This sets the right Host header → should be 200/OK:
curl -i -H 'Host: n8n.localtest.me' http://127.0.0.1:8081/

# 2) This misses Host rule → will be 404 route not found:
curl -i http://127.0.0.1:8081/

# 3) 8443 has no n8n router bound → will be 404 route not found:
curl -i -H 'Host: n8n.localtest.me' https://127.0.0.1:8443/  || true
```

If (1) works but the browser still shows 404, you’re likely visiting the wrong URL. Use **[http://n8n.localtest.me:8081/](http://n8n.localtest.me:8081/)** (not 127.0.0.1, not https, not 8443).

---

## 2) Step-by-step: bring the stack up and confirm routing

```bash
cd ~/live/dinesh/llm-chatbot-python/n8n-stack
mkdir -p n8n/logs n8n/local-files n8n/custom-nodes
chmod -R 777 n8n/logs
docker compose build
docker compose up -d
docker compose ps
```

Routing checks:

```bash
# DNS: localtest.me → 127.0.0.1
ping -c 1 n8n.localtest.me

# Through Traefik with a correct Host header:
curl -i -H 'Host: n8n.localtest.me' http://127.0.0.1:8081/

# Watch Traefik while you load the page:
docker logs n8n_stack-traefik-1 --tail=200
```

**Expected:** Traefik logs show the request hitting router `n8n` and forwarding to service port **5678**.
If you still get 404, double-check the exact URL in your browser’s address bar.

---

## 3) Why 8443 shows “route not found” (and what to do)

* Your compose **defines** entrypoint **websecure** on **:8443**, but **no router** is attached to it.
* You also didn’t configure TLS certs for that router.

**Result:** requests on **8443** have **no matching router** → **404 route not found**.
**Action:** For now, **don’t use 8443**. Stick to:

```
http://n8n.localtest.me:8081/
http://api.localtest.me:8081/
```

*(When you’re ready for HTTPS later, we can add a proper TLS router on 8443. No compose changes now.)*

---

## 4) Fixing Google OAuth (local) — in depth, with your exact URLs

### 4.1 Put the consent screen in **Testing** and add your account

* Open: `https://console.cloud.google.com/apis/credentials/consent`

  * Set **Publishing status** → **Testing**
  * Add your Google account under **Test users** → **Save**
    **Why:** Testing allows `http://` redirects and unverified domains, but **only** for added test users. Production requires `https://` and domain verification.

### 4.2 Register the **exact** redirect URI that n8n uses

* Open: `https://console.cloud.google.com/apis/credentials`

  * Edit your **OAuth 2.0 Client (Web)**
  * In **Authorized redirect URIs**, add **exactly**:

    ```
    http://n8n.localtest.me:8081/rest/oauth2-credential/callback
    ```
  * Save.

**Why:** Google checks the redirect URI character-for-character (scheme, host, **port**, path). Any mismatch → `redirect_uri_mismatch (400)`.

### 4.3 Enable the Google APIs you’ll call

* Open: `https://console.cloud.google.com/apis/library`
  Enable as needed:

  * **Gmail API**
  * **Google Sheets API**
  * **Google Drive API** (often required with Sheets)
  * **People API** (contacts/profile, if used)
  * **Calendar API** (if used)

**Why:** If the API is off, calls fail with `SERVICE_DISABLED (403)` even when OAuth succeeds.
Allow **2–5 minutes** for the “Enable” action to propagate.

### 4.4 Create/connect the credential in n8n

* n8n → **Settings → Credentials → New → Google OAuth2** (or the node-specific Google credential)
* Paste **Client ID** and **Client Secret** from Google
* Add scopes you need, for example:

  * Gmail read: `https://www.googleapis.com/auth/gmail.readonly`
  * Sheets read: `https://www.googleapis.com/auth/spreadsheets.readonly`
* Click **Connect OAuth**, approve Google’s prompt → Google redirects back to:

  ```
  http://n8n.localtest.me:8081/rest/oauth2-credential/callback
  ```
* The n8n credential should show **Connected**.

---

## 5) Google errors → exact causes → exact fixes

**`Error 400: redirect_uri_mismatch`**

* **Cause:** The URI in Google doesn’t match the one sent by n8n.
* **Fix:** Add the exact URI you’re using:
  `http://n8n.localtest.me:8081/rest/oauth2-credential/callback`

**“Invalid redirect: URI must use https\://”**

* **Cause:** Consent screen is **Production**; `http://` is not allowed.
* **Fix (local):** switch to **Testing** and retry.
* **Fix (prod):** move n8n to **HTTPS** (real domain), then register `https://…/rest/oauth2-credential/callback`.

**“Access blocked: domain not verified” (403 access\_denied)**

* **Cause:** Using an unverified domain (e.g., `localtest.me`) with **Production** consent; or you’re not listed as a **Test user** in Testing.
* **Fix (local):** keep **Testing** and add yourself as a **Test user**.
* **Fix (prod):** use a domain you own, verify it, and serve HTTPS.

**`SERVICE_DISABLED (403)` for Gmail/Sheets/Drive**

* **Cause:** The API isn’t enabled in your Google project.
* **Fix:** Enable the API in **API Library**, wait a few minutes, and retry.

---

## 6) If you still hit a **500** on the n8n UI

1. **Permissions**

   ```bash
   chmod -R 777 n8n/logs
   ```

   Look for `EACCES` / `permission denied` in:

   ```bash
   docker logs n8n_stack-n8n-1 --tail=200
   ```

2. **One n8n only (SQLite lock)**

   ```bash
   docker ps | grep n8n
   ```

   Ensure only **one** `n8n_stack-n8n-1` is running. If you previously ran another n8n, stop it.

3. **Check Traefik for routing errors**

   ```bash
   docker logs n8n_stack-traefik-1 --tail=200
   ```

   If you see “bad gateway” or “route not found”, re-check you’re visiting **[http://n8n.localtest.me:8081/](http://n8n.localtest.me:8081/)** and not 127.0.0.1 or 8443.

---

## 7) Note on Loki restarting (seen in your `docker ps`)

Your `loki` container is **Restarting**. That’s unrelated to n8n routing, but easy to check:

```bash
docker logs n8n_stack-loki-1 --tail=200
```

Typical causes:

* Bad or missing config at `./loki/config.yml` (typo/indentation).
* The container can’t read the file (path or permissions).
* Port conflict is rare here since you map `127.0.0.1:3100:3100`.

**What to do:**

* Confirm the file exists and is readable:

  ```bash
  ls -l ./loki/config.yml
  ```
* If logs show a YAML parse error, fix `config.yml` (spacing/keys).
* After fixes:

  ```bash
  docker compose up -d loki
  ```

---

## 8) The only URLs you should use (match your compose)

**n8n (via Traefik, HTTP):**
`http://n8n.localtest.me:8081/`

**automation-api (via Traefik, HTTP):**
`http://api.localtest.me:8081/`

**Grafana:**
`http://127.0.0.1:3030/`

**Loki:**

* Base: `http://127.0.0.1:3100/`
* Ready: `http://127.0.0.1:3100/ready`
* Metrics: `http://127.0.0.1:3100/metrics`

**Google Console:**

* Credentials (OAuth clients): `https://console.cloud.google.com/apis/credentials`
* OAuth Consent Screen: `https://console.cloud.google.com/apis/credentials/consent`
* API Library: `https://console.cloud.google.com/apis/library`

**Redirect URI to register (exactly, for your stack):**
`http://n8n.localtest.me:8081/rest/oauth2-credential/callback`

---

## 9) Minimal screenshots to add in your README (placeholders)

* Consent in Testing mode
  `![Consent — Testing](docs/images/consent-testing.png)`
* OAuth client: add redirect URI
  `![OAuth Redirect URIs](docs/images/oauth-client-redirects.png)`
* Enable Gmail API
  `![Enable Gmail API](docs/images/enable-gmail-api.png)`
* n8n Google credential connected
  `![n8n Google Connected](docs/images/n8n-google-connected.png)`

(Keep to these four; they’re sufficient.)

---

### Summary

* **8081 “route not found”** → you’re not sending **Host: n8n.localtest.me** or you’re hitting the wrong port. Use **[http://n8n.localtest.me:8081/](http://n8n.localtest.me:8081/)**.
* **8443 “route not found”** → expected; no TLS router is bound to websecure. Don’t use 8443 right now.
* **Google OAuth** → Testing mode + Test user, register **exact** redirect URI, enable APIs.
* **500s** → check log permissions, ensure a single n8n instance, and review logs for the precise error.
