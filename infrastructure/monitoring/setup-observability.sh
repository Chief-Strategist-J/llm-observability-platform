#!/bin/bash

# Complete Observability Stack Setup Script
# Sets up Loki, Promtail, Prometheus, OpenTelemetry Collector, Tempo, and Grafana

set -e

echo "🚀 Setting up Complete Observability Stack"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create monitoring network if it doesn't exist
print_status "Creating monitoring network..."
docker network create monitoring-network --driver bridge 2>/dev/null || print_warning "Network already exists"

# Start services in order

# 1. Start Loki (log storage)
print_status "Starting Loki..."
cd component/loki
docker compose -f logger-loki-compose.yaml up -d
cd ../..

# 2. Wait for Loki to be ready
print_status "Waiting for Loki to be ready..."
sleep 10

# 3. Start Tempo (trace storage)
print_status "Starting Tempo..."
cd component/tempo
docker compose -f tempo-compose.yaml up -d
cd ../..

# 4. Wait for Tempo
print_status "Waiting for Tempo..."
sleep 5

# 5. Start Prometheus (metrics collection)
print_status "Starting Prometheus..."
cd component/prometheus
docker compose -f prometheus-compose.yaml up -d
cd ../..

# 6. Wait for Prometheus
print_status "Waiting for Prometheus..."
sleep 10

# 7. Start OpenTelemetry Collector (traces, metrics, logs)
print_status "Starting OpenTelemetry Collector..."
cd component/otel
docker compose -f otel-collector-compose.yaml up -d
cd ../..

# 8. Wait for OTEL Collector
print_status "Waiting for OpenTelemetry Collector..."
sleep 5

# 9. Start Promtail (log collection)
print_status "Starting Promtail..."
cd ../loki
docker compose -f logger-loki-compose.yaml up -d promtail
cd ..

# 10. Start Grafana (visualization)
print_status "Starting Grafana..."
cd ../grafana
docker compose -f dashboard-grafana-compose.yaml up -d grafana-development
cd ..

# Final wait
print_status "Waiting for all services to be fully ready..."
sleep 15

# Verification
print_status "Verifying services..."
echo ""

echo "📊 Container Status:"
docker ps --filter "name=loki\|promtail\|prometheus\|otel-collector\|tempo\|grafana" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🌐 Service Connectivity Tests:"
echo ""

# Test Loki
if curl -s "http://localhost:31090/ready" >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}Loki API${NC} - Ready"
else
    echo -e "❌ ${RED}Loki API${NC} - Not responding"
fi

# Test Prometheus
if curl -s "http://localhost:9090/-/ready" >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}Prometheus${NC} - Ready"
else
    echo -e "❌ ${RED}Prometheus${NC} - Not responding"
fi

# Test Tempo
if curl -s "http://localhost:3200/ready" >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}Tempo${NC} - Ready"
else
    echo -e "❌ ${RED}Tempo${NC} - Not responding"
fi

# Test Grafana
if curl -s "http://localhost:31001/api/health" >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}Grafana${NC} - Ready"
else
    echo -e "❌ ${RED}Grafana${NC} - Not responding"
fi

echo ""
print_status "🎉 Complete Observability Stack is ready!"
echo ""
echo "📊 Access Grafana at: http://localhost:31001"
echo "🔐 Login: admin / SuperSecret123!"
echo ""
echo "🔍 Available Data Sources:"
echo "  • Loki (Logs): http://loki:3100"
echo "  • Prometheus (Metrics): http://prometheus:9090"
echo "  • Tempo (Traces): http://tempo:3200"
echo ""
echo "📡 OpenTelemetry Collector endpoints:"
echo "  • OTLP gRPC: localhost:4317"
echo "  • OTLP HTTP: localhost:4318"
echo "  • Jaeger: localhost:14250"
echo "  • Zipkin: localhost:9411"
echo ""
echo "🚀 Ready to collect logs, metrics, and traces from your applications!"
