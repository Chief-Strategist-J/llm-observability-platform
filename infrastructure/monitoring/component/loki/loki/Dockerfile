# loki/Dockerfile
FROM grafana/loki:2.8.2

USER root

# Create required directories (including chunks) and set ownership to UID 472 (grafana user)
RUN mkdir -p /loki/development /loki/staging /loki/production /loki/wal /loki/chunks && \
    chmod -R 755 /loki && \
    chown -R 472:472 /loki

# Copy Loki config into the image
COPY loki-local-config.yaml /etc/loki/loki-local-config.yaml
RUN chmod 644 /etc/loki/loki-local-config.yaml && chown 472:472 /etc/loki/loki-local-config.yaml

EXPOSE 3100

# Run as grafana user (UID 472)
USER 472

ENTRYPOINT ["/usr/bin/loki"]
CMD ["-config.file=/etc/loki/loki-local-config.yaml"]
