#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/config/kafka-docker-compose.yaml"

ACTION=${1:-up}

case $ACTION in
    up)
        echo "Starting Kafka stack..."
        docker-compose -f "$COMPOSE_FILE" up -d
        echo "Kafka stack started successfully"
        echo "Kafka UI available at http://localhost:8082"
        ;;
    down)
        echo "Stopping Kafka stack..."
        docker-compose -f "$COMPOSE_FILE" down
        echo "Kafka stack stopped"
        ;;
    restart)
        echo "Restarting Kafka stack..."
        docker-compose -f "$COMPOSE_FILE" restart
        echo "Kafka stack restarted"
        ;;
    logs)
        echo "Showing Kafka logs..."
        docker-compose -f "$COMPOSE_FILE" logs -f
        ;;
    status)
        echo "Kafka stack status:"
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    *)
        echo "Usage: $0 {up|down|restart|logs|status}"
        echo "  up      - Start Kafka stack"
        echo "  down    - Stop Kafka stack"
        echo "  restart - Restart Kafka stack"
        echo "  logs    - Show Kafka logs"
        echo "  status  - Show Kafka status"
        exit 1
        ;;
esac
