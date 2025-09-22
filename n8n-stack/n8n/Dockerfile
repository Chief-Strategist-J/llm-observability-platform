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
