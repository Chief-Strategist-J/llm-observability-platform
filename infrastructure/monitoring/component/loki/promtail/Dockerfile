# promtail/Dockerfile
FROM grafana/promtail:2.8.2

USER root

# Create config directory and set ownership
RUN mkdir -p /etc/promtail && \
    chmod -R 755 /etc/promtail && \
    chown -R 472:472 /etc/promtail

# Copy Promtail config into the image
COPY promtail-config.yaml /etc/promtail/promtail-config.yaml
RUN chmod 644 /etc/promtail/promtail-config.yaml && chown 472:472 /etc/promtail/promtail-config.yaml

EXPOSE 9080

USER 472

# Use base image entrypoint; pass the config file via CMD
CMD ["-config.file=/etc/promtail/promtail-config.yaml"]
