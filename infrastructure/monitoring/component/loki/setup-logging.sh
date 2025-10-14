#!/bin/bash

# Loki + Promtail Setup Script
# This script sets up and starts the complete logging infrastructure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "🚀 Setting up Loki + Promtail logging infrastructure..."

# Function to check if Docker network exists
create_network() {
    if ! docker network inspect monitoring-network >/dev/null 2>&1; then
        echo "📡 Creating monitoring network..."
        docker network create monitoring-network
    else
        echo "📡 Monitoring network already exists"
    fi
}

# Function to set permissions
set_permissions() {
    echo "🔐 Setting proper permissions..."

    # Set ownership for storage directories (UID 472 for Grafana/Loki containers)
    sudo chown -R 472:472 "$PROJECT_ROOT/component/grafana/storage" 2>/dev/null || true
    sudo chown -R 472:472 "$PROJECT_ROOT/component/loki/loki/data" 2>/dev/null || true
    sudo chown -R 472:472 "$PROJECT_ROOT/component/loki/promtail" 2>/dev/null || true

    # Set readable permissions
    sudo chmod -R a+rX "$PROJECT_ROOT/component/grafana/storage" 2>/dev/null || true
    sudo chmod -R a+rX "$PROJECT_ROOT/component/loki/loki/data" 2>/dev/null || true
    sudo chmod -R a+rX "$PROJECT_ROOT/component/loki/promtail" 2>/dev/null || true

    echo "✅ Permissions set"
}

# Function to build and start services
start_services() {
    echo "🐳 Building and starting Loki + Promtail..."

    cd "$SCRIPT_DIR"

    # Build the images
    echo "🔨 Building Docker images..."
    docker compose -f logger-loki-compose.yaml build

    # Start the services
    echo "🚀 Starting services..."
    docker compose -f logger-loki-compose.yaml up -d

    echo "✅ Loki + Promtail started successfully!"
}

# Function to show status
show_status() {
    echo "📊 Service Status:"
    docker ps --filter "name=loki" --filter "name=promtail" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

    echo ""
    echo "🌐 Access Information:"
    echo "Loki API: http://localhost:31090"
    echo "Grafana:  http://localhost:31001 (development)"
    echo ""
    echo "📝 Example log query in Grafana:"
    echo "{job=\"python-app\", env=\"development\"} |= \"error\""
}

# Main execution
main() {
    echo "🔧 Loki + Promtail Setup Starting..."
    echo "=================================="

    create_network
    set_permissions
    start_services
    show_status

    echo ""
    echo "🎉 Setup Complete!"
    echo ""
    echo "Next steps:"
    echo "1. Start your Grafana: cd ../grafana && ./script/grafana-control.sh"
    echo "2. Add the Python logger to your apps (see python_logger_example.py)"
    echo "3. Check logs in Grafana: Explore → Loki → {job=\"python-app\"}"
}

main "$@"
