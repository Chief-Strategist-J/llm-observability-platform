FROM grafana/loki:2.8.2

USER root

# Create data directories for each environment
RUN mkdir -p /loki/development /loki/staging /loki/production /loki/wal && \
    chmod -R 755 /loki && \
    chown -R 472:472 /loki

# Copy Loki config
COPY loki-local-config.yaml /etc/loki/loki-local-config.yaml
RUN chmod 644 /etc/loki/loki-local-config.yaml && chown 472:472 /etc/loki/loki-local-config.yaml

EXPOSE 3100
USER 472

CMD ["-config.file=/etc/loki/loki-local-config.yaml"]
