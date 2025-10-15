FROM grafana/tempo:latest

# Create necessary directories
RUN mkdir -p /etc/tempo /tmp/tempo

# Copy configuration
COPY tempo-config.yaml /etc/tempo/tempo-config.yaml

EXPOSE 4317 4318 14268

CMD ["-config.file=/etc/tempo/tempo-config.yaml"]
