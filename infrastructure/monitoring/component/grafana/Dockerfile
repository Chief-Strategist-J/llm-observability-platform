FROM grafana/grafana:11.1.0

# Switch to root to set up permissions
USER root

# Create necessary directories with proper permissions
RUN mkdir -p /var/lib/grafana/plugins /var/lib/grafana/dashboards /var/log/grafana && \
    chmod -R 755 /var/lib/grafana /var/log/grafana && \
    chown -R 472:472 /var/lib/grafana /var/log/grafana

# Copy environment configuration files
COPY grafana.env /etc/grafana/grafana.env
COPY grafana-secrets.env /etc/grafana/grafana-secrets.env

# Set proper permissions for config files
RUN chmod 644 /etc/grafana/grafana.env && \
    chmod 600 /etc/grafana/grafana-secrets.env && \
    chown 472:472 /etc/grafana/grafana.env /etc/grafana/grafana-secrets.env

# Set the working directory
WORKDIR /etc/grafana

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

# Switch to grafana user for security
USER grafana

# Start Grafana
CMD ["grafana-server", "--homepath=/usr/share/grafana", "--config=/etc/grafana/grafana.ini"]
