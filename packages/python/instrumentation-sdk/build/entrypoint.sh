#!/bin/bash
set -e

mkdir -p /var/log/app

if [ "$WITH_KAFKA" = "true" ]; then
    service postgresql start
    sleep 3
    su - postgres -c "psql -c \"CREATE USER admin WITH PASSWORD 'password' SUPERUSER;\"" || true
    su - postgres -c "psql -c \"CREATE DATABASE llm_observability OWNER admin;\"" || true
    PGPASSWORD=password psql -h localhost -U admin -d llm_observability -f /app/database/migrations/postgres/0001_init.sql || true
    KAFKA_CLUSTER_ID=$(/opt/kafka/bin/kafka-storage.sh random-uuid)
    /opt/kafka/bin/kafka-storage.sh format -t "$KAFKA_CLUSTER_ID" -c /opt/kafka/config/kraft/server.properties || true
    /opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/kraft/server.properties > /var/log/app/kafka.log 2>&1 &
    sleep 5
    if [ -z "$KAFKA_BOOTSTRAP_SERVERS" ]; then
        export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
    fi
    KAFKA_BOOTSTRAP_SERVER="localhost:9092" /app/scripts/setup_kafka.sh
fi

tempo -config.file=/app/build/tempo-config.yaml > /var/log/app/tempo.log 2>&1 &
echo "Tempo started successfully!"
sleep 2

cd /usr/share/grafana
GF_DATABASE_WAL=true GF_DATABASE_TRANSACTION_RETRIES=100 GF_DATABASE_QUERY_RETRIES=100 grafana-server --homepath=/usr/share/grafana --config=/etc/grafana/grafana.ini > /var/log/app/grafana.log 2>&1 &
cd /app
echo "Grafana started successfully!"
sleep 6

prometheus --config.file=/etc/prometheus/prometheus.yml > /var/log/app/prometheus.log 2>&1 &
echo "Prometheus started successfully!"

sleep 2

echo "Starting FastAPI Application..."
exec uvicorn src.api.rest.v1.app:app --host 0.0.0.0 --port 8000
