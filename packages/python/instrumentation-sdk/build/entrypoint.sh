#!/bin/bash
set -e

mkdir -p /var/log/app

tempo -config.file=/app/build/tempo-config.yaml > /var/log/app/tempo.log 2>&1 &
echo "Tempo started successfully!"

grafana-server --homepath=/usr/share/grafana --config=/etc/grafana/grafana.ini > /var/log/app/grafana.log 2>&1 &
echo "Grafana started successfully!"

sleep 2

echo "Starting FastAPI Application..."
exec uvicorn src.api.rest.v1.app:app --host 0.0.0.0 --port 8000
