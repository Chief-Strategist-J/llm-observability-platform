# HTTPS Configuration for Production

This document provides instructions for configuring HTTPS for the Messaging API in production environments.

## Prerequisites

- SSL/TLS certificate (from Let's Encrypt, your organization, or self-signed for testing)
- Domain name configured to point to your server
- Uvicorn server (or another ASGI server)

## Option 1: Using Uvicorn with SSL Certificate

### Generate Self-Signed Certificate (for testing)

```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

### Start Server with HTTPS

```bash
uvicorn application.api.v1.main:app --host 0.0.0.0 --port 443 --ssl-keyfile key.pem --ssl-certfile cert.pem
```

## Option 2: Using Nginx Reverse Proxy (Recommended for Production)

### Install Nginx

```bash
sudo apt-get update
sudo apt-get install nginx
```

### Configure Nginx

Create `/etc/nginx/sites-available/messaging-api`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Enable Configuration

```bash
sudo ln -s /etc/nginx/sites-available/messaging-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Start FastAPI Application

```bash
uvicorn application.api.v1.main:app --host 127.0.0.1 --port 8000
```

## Option 3: Using Let's Encrypt with Certbot

### Install Certbot

```bash
sudo apt-get install certbot python3-certbot-nginx
```

### Obtain Certificate

```bash
sudo certbot --nginx -d your-domain.com
```

Certbot will automatically configure Nginx with HTTPS.

## Security Headers

Add security headers to your FastAPI application in `main.py`:

```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Redirect HTTP to HTTPS
app.add_middleware(HTTPSRedirectMiddleware)

# Only allow specific hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["your-domain.com", "www.your-domain.com"]
)
```

## Environment Variables

Store sensitive configuration in environment variables:

```bash
export SSL_CERT_PATH=/path/to/cert.pem
export SSL_KEY_PATH=/path/to/key.pem
export DOMAIN_NAME=your-domain.com
```

Update `main.py` to use environment variables:

```python
import os

ssl_cert = os.getenv("SSL_CERT_PATH")
ssl_key = os.getenv("SSL_KEY_PATH")
```

## Testing HTTPS Configuration

### Test with curl

```bash
curl -k https://localhost/api/v1/health
```

### Test with browser

Navigate to `https://your-domain.com/docs` to view Swagger documentation.

## Production Checklist

- [ ] Obtain valid SSL/TLS certificate
- [ ] Configure HTTPS on server
- [ ] Enable HTTP to HTTPS redirect
- [ ] Add security headers
- [ ] Configure firewall to allow HTTPS (port 443)
- [ ] Test HTTPS configuration
- [ ] Set up certificate auto-renewal (if using Let's Encrypt)
- [ ] Monitor certificate expiration
- [ ] Update CORS settings for production domain
- [ ] Configure rate limiting for production traffic

## Troubleshooting

### Certificate Issues

If you see certificate errors:
- Verify certificate path is correct
- Check certificate expiration date
- Ensure domain name matches certificate

### Port Issues

If port 443 is blocked:
- Check firewall rules: `sudo ufw status`
- Allow HTTPS: `sudo ufw allow 443/tcp`

### Nginx Issues

Check Nginx logs:
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## Additional Resources

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
