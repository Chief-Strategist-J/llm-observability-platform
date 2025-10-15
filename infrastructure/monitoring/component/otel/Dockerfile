FROM otel/opentelemetry-collector-contrib:0.100.0

# Create necessary directories
RUN mkdir -p /etc/otel && \
    chmod -R 755 /etc/otel

# Copy configuration
COPY otel-config.yaml /etc/otel/otel-config.yaml

EXPOSE 4317 4318 8888 8889 13133

CMD ["--config-file=/etc/otel/otel-config.yaml"]
