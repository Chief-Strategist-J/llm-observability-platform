# Secure HTTPS Setup for Traefik (Local / Development)

## Overview

Your current Traefik setup uses the built-in “TRAEFIK DEFAULT CERT.” Browsers distrust that certificate, so you see “Not Secure.”
This document shows how to replace it with a locally trusted TLS certificate using mkcert, so that browsers will accept the hostname without warnings — ideal for local development.

---

## Directory Layout

```
infrastructure/orchestrator/config/docker/traefik/
├── config/  
│   └── traefik-dynamic-docker.yaml  
├── host_manage_activity.py  
├── traefik_activity.py  
├── virtual_ip_manage_activity.py  
└── …  
```

You will add a new subdirectory `certs/` under this path to store TLS keys and certificates.

---

## Prerequisites

* Docker & Docker Compose (you already have that)
* Local machine shell access (Linux / Ubuntu)
* mkcert dependencies (for certificate generation)

---

## Step-by-Step Instructions

### 1. Install mkcert and its CA

```bash
sudo apt update  
sudo apt install -y libnss3-tools  
cd /tmp  
curl -JLO "https://dl.filippo.io/mkcert/latest?for=linux/amd64"  
chmod +x mkcert*  
sudo mv mkcert* /usr/local/bin/mkcert  
mkcert -install  
```

This installs mkcert and adds its local CA to your system/browser trust store. ([GitHub][1])

---

### 2. Create a certs directory for Traefik

From your project root:

```bash
mkdir -p infrastructure/orchestrator/config/docker/traefik/certs
```

---

### 3. Generate a certificate for your hostname

```bash
cd infrastructure/orchestrator/config/docker/traefik/certs
mkcert scaibu.traefik
cd ../../../../../..
```

This produces two files:

* `scaibu.traefik.pem` (certificate)
* `scaibu.traefik-key.pem` (private key) ([GitHub][1])

---

### 4. Update Traefik dynamic configuration to use the certificate


### File: `infrastructure/orchestrator/config/docker/traefik/config/traefik_dynamic_tls.yaml`

```yaml
tls:
  certificates:
    - certFile: "/certs/scaibu.traefik.pem"
      keyFile: "/certs/scaibu.traefik-key.pem"

  stores:
    default:
      defaultCertificate:
        certFile: "/certs/scaibu.traefik.pem"
        keyFile: "/certs/scaibu.traefik-key.pem"
```

---

## 📌 Explanation of Key Changes

* We added a **volume mount** for `./infrastructure/orchestrator/config/docker/traefik/certs` → `/certs` inside the container. This allows Traefik to read your TLS certificate files.
* We switched from using Let’s Encrypt / ACME to using a **file provider** (via `--providers.file.filename`) for TLS. That ensures Traefik loads your custom certificate. This is recommended when using local/private domains. ([Traefik Labs Community Forum][1])
* The `traefik_dynamic_tls.yaml` file defines a TLS store + default certificate. This tells Traefik: use this cert by default for any TLS request. ([Traefik Labs Community Forum][2])
* The router for the dashboard (`Host(\`scaibu.traefik`)`) is configured to use `tls: "true"`. That enables HTTPS for that hostname.

---
---

### 5. Update your Docker Compose to mount the certs directory

In your `docker-compose.yml`, under the Traefik service, modify the `volumes` section to include:

```yaml
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik-certs:/letsencrypt
      - traefik-config:/etc/traefik
      - ./infrastructure/orchestrator/config/docker/traefik/certs:/certs:ro
      - ./infrastructure/orchestrator/config/docker/traefik/config/traefik_dynamic_tls.yaml:/etc/traefik/traefik_dynamic_tls.yaml:ro
```

In your `docker-compose.yml`, under the Traefik service, modify the `command` section to include:

```yaml
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedByDefault=false"
      - "--providers.docker.endpoint=unix:///var/run/docker.sock"
      - "--providers.docker.watch=true"
      - "--providers.file.filename=/etc/traefik/traefik_dynamic_tls.yaml"
      - "--providers.file.watch=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      - "--entrypoints.web.http.redirections.entrypoint.permanent=true"
      - "--api.dashboard=true"
      - "--api.insecure=false"
      - "--ping=true"
      - "--log.level=INFO"
      - "--log.format=json"
      - "--accesslog=true"
      - "--accesslog.format=json"
      - "--accesslog.fields.headers.defaultmode=keep"
      - "--metrics.prometheus=true"
      - "--metrics.prometheus.addEntryPointsLabels=true"
      - "--metrics.prometheus.addServicesLabels=true"
      - "--metrics.prometheus.addRoutersLabels=true"
```


---

### 6. Disable ACME / Let’s Encrypt since domain is local

Since `scaibu.traefik` is not a publicly reachable domain, the ACME challenge will always fail. Remove or comment out all ACME-related command flags in the `command:` section of your compose file:

```diff
- "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
- "--certificatesresolvers.letsencrypt.acme.email=admin@scaibu.local"
- "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
- "--certificatesresolvers.letsencrypt.acme.caserver=..."
```

This avoids Traefik trying and falling back to a self-signed default cert. Community docs confirm that when using custom certs, ACME/Let’s Encrypt should be disabled. ([Traefik Labs Community Forum][3])

---

### 7. Restart Traefik container

```bash
docker restart traefik-scaibu
```

Check logs to confirm it loads your certificate:

```bash
docker logs traefik-scaibu | grep -i "default certificate"
```

You should see a log entry indicating the custom certificate is in use.

---

## Verification

1. Open your browser at:

   ```
   https://scaibu.traefik
   ```

2. You should see:

   * A secure padlock icon
   * Certificate issued for `scaibu.traefik` by “mkcert development CA” (or similar)
   * No security warnings
   * Full HTTPS functioning

---

## Why This Works

* mkcert generates a certificate signed by a **local CA** trusted by your system/browser. ([GitHub][1])
* Traefik can be configured (with `providers.file` + TLS store) to serve custom TLS certs from specified paths. ([Traefik Labs Community Forum][4])
* No more self-signed default cert → browsers trust the connection → “secure” padlock appears

---

## What You Should Remove / Avoid

* Don’t rely on ACME / Let’s Encrypt for local domains — challenge will fail.
* Don’t enable TLS before mounting correct certs.
* Keep private keys secure; do not commit them to public repo.

---

## Additional Resources

* “Using HTTPS certificates with Traefik and Docker for Local Development” — describes mkcert + Traefik setup. ([putzisan.com][5])
* Official mkcert repo — for cross-platform installation and trusted CA creation. ([GitHub][1])
* Example project combining mkcert + Traefik + Docker Compose for localhost HTTPS. ([GitHub][6])

===
Good: I can give you a **full `docker-compose.yml`** that includes mounting the certs and referencing a custom certificate (not Let’s Encrypt), plus a sample **dynamic TLS configuration file** for Traefik, so you can drop them into your project and have TLS enabled with your own certificate.

---

### ⚠ Important Notes

* Because you're using a self-signed or locally-trusted certificate (e.g. from mkcert), ensure the certificate’s CA is trusted by your OS/browser. Otherwise the browser will still warn. ([Mborne][3])
* Do **not** keep both Let’s Encrypt and the custom file-provider enabled simultaneously — they can conflict. Use one or the other.
* Every time you regenerate the certificate, restart Traefik so it loads the new certificate.

