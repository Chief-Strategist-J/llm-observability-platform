FROM prom/prometheus:latest

# Create necessary directories
RUN mkdir -p /etc/prometheus /prometheus

# Copy configuration
COPY prometheus.yml /etc/prometheus/prometheus.yml

EXPOSE 9090

# Use proper CMD format for Prometheus
CMD ["--config.file=/etc/prometheus/prometheus.yml", \
     "--storage.tsdb.path=/prometheus", \
     "--web.console.libraries=/usr/share/prometheus/console_libraries", \
     "--web.console.templates=/usr/share/prometheus/consoles", \
     "--web.enable-lifecycle"]
