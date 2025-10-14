FROM grafana/promtail:2.8.2

USER root

# Create necessary directories (but not the mounted host-storage path)
RUN mkdir -p /etc/promtail && \
    chmod -R 755 /etc/promtail && \
    chown -R 472:472 /etc/promtail

# Copy Promtail config
COPY promtail-config.yaml /etc/promtail/promtail-config.yaml
RUN chmod 644 /etc/promtail/promtail-config.yaml && chown 472:472 /etc/promtail/promtail-config.yaml

EXPOSE 9080

USER 472

CMD ["-config.file=/etc/promtail/promtail-config.yaml"]
