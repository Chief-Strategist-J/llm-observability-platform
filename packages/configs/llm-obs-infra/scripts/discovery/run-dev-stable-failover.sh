#!/usr/bin/env bash

# ==============================================================================
# Service Discovery & Active-Passive Dev/Stable Failover Control Script
# Package: packages/configs/llm-obs-infra
# ==============================================================================

set -euo pipefail

# Color Codes for Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Determine Script & Repo Root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

REGISTRY_URL="http://localhost:31426"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prereqs() {
    log_info "Verifying Docker environment prerequisites..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH."
        exit 1
    fi

    if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not available."
        exit 1
    fi
    log_success "Docker environment OK!"
}

get_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

start_stack() {
    check_prereqs
    log_info "Ensuring 'llmobs-network' Docker network exists..."
    docker network create llmobs-network 2>/dev/null || true

    log_info "Starting Service Discovery Registry container in Docker..."
    cd "${INFRA_ROOT}"
    COMPOSE_CMD=$(get_compose_cmd)
    
    ${COMPOSE_CMD} up -d --build llmobs-service-registry
    
    log_info "Waiting for Service Registry to become healthy on port 31426..."
    local retries=15
    while [ $retries -gt 0 ]; do
        if curl -s "${REGISTRY_URL}/health" | grep -q '"status"'; then
            log_success "Service Registry is ONLINE at ${REGISTRY_URL}"
            break
        fi
        sleep 1
        ((retries--))
    done

    if [ $retries -eq 0 ]; then
        log_warn "Service Registry health check timed out. Displaying container logs:"
        ${COMPOSE_CMD} logs --tail=20 llmobs-service-registry
        exit 1
    fi

    log_success "Service Discovery container started successfully!"
    show_status
}

show_status() {
    log_info "Fetching Active Services & Devices from Registry (${REGISTRY_URL}/v1/services)..."
    echo -e "${CYAN}----------------------------------------------------------------------${NC}"
    if curl -s "${REGISTRY_URL}/v1/services" | grep -q '"success"'; then
        curl -s "${REGISTRY_URL}/v1/services" | tr -d '\r'
    else
        log_warn "Unable to fetch services or registry is offline."
    fi
    echo -e "\n${CYAN}----------------------------------------------------------------------${NC}"
}

search_service() {
    local target_svc="${1:-}"
    if [ -z "$target_svc" ]; then
        log_error "Please specify a service name to search (e.g. $0 search clickhouse)"
        exit 1
    fi

    log_info "Searching and resolving endpoint for service '${target_svc}'..."
    echo -e "${CYAN}----------------------------------------------------------------------${NC}"
    curl -s "${REGISTRY_URL}/v1/resolve?service=${target_svc}"
    echo -e "\n${CYAN}----------------------------------------------------------------------${NC}"
}

register_custom_service() {
    local name="${1:-custom-service}"
    local port="${2:-8080}"
    local host="${3:-localhost}"

    log_info "Registering Custom Service '${name}' on ${host}:${port}..."
    curl -s -X POST "${REGISTRY_URL}/v1/register" \
      -H "Content-Type: application/json" \
      -d "{
        \"name\": \"${name}\",
        \"host\": \"${host}\",
        \"port\": ${port},
        \"protocol\": \"http\",
        \"healthCheck\": {
          \"protocol\": \"http\",
          \"path\": \"/health\"
        }
      }"
    echo ""
    log_success "Registered custom service '${name}'!"
    search_service "${name}"
}

register_demo_devices() {
    log_info "Registering Demo Services (v2-dev on :8082, v1-stable on :8081)..."
    
    # Register v2-dev Primary (Weight 100)
    curl -s -X POST "${REGISTRY_URL}/v1/register" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "demo-analytics",
        "host": "127.0.0.1",
        "port": 8082,
        "protocol": "http",
        "version": "v2-dev",
        "weight": 100,
        "healthCheck": {
          "protocol": "http",
          "path": "/health"
        }
      }' > /dev/null && log_success "Registered Primary Instance: v2-dev (Weight: 100, Port: 8082)"

    # Register v1-stable Fallback (Weight 1)
    curl -s -X POST "${REGISTRY_URL}/v1/register" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "demo-analytics",
        "host": "127.0.0.1",
        "port": 8081,
        "protocol": "http",
        "version": "v1-stable",
        "weight": 1,
        "healthCheck": {
          "protocol": "http",
          "path": "/health"
        }
      }' > /dev/null && log_success "Registered Fallback Instance: v1-stable (Weight: 1, Port: 8081)"

    show_status
}

stop_stack() {
    log_info "Stopping Docker Environment Stack..."
    cd "${INFRA_ROOT}"
    COMPOSE_CMD=$(get_compose_cmd)
    ${COMPOSE_CMD} stop llmobs-service-registry
    log_success "Service Registry container stopped."
}

usage() {
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "${GREEN} Service Discovery & Dev/Stable Failover Runner ${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start                       Build & start Service Registry container in Docker"
    echo "  status                      List all registered services & devices in memory"
    echo "  search <name>               Search and resolve a specific service (e.g. clickhouse, redis)"
    echo "  register-custom <name> <port> Register a custom device/service dynamically"
    echo "  register-demo               Register demo v2-dev (8082) & v1-stable (8081) devices"
    echo "  stop                        Stop Service Registry Docker container"
    echo ""
}

case "${1:-}" in
    start)
        start_stack
        ;;
    status)
        show_status
        ;;
    search)
        search_service "${2:-}"
        ;;
    register-custom)
        register_custom_service "${2:-}" "${3:-8080}" "${4:-localhost}"
        ;;
    register-demo)
        register_demo_devices
        ;;
    stop)
        stop_stack
        ;;
    *)
        usage
        ;;
esac
