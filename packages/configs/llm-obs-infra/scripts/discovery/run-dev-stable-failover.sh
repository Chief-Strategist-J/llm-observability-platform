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
GATEWAY_URL="http://localhost:31410"

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
    log_info "Starting Service Discovery & Traefik Infrastructure Stack in Docker..."
    
    cd "${INFRA_ROOT}"
    COMPOSE_CMD=$(get_compose_cmd)
    
    # 1. Start core service discovery registry and Traefik
    ${COMPOSE_CMD} up -d --build
    
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
        log_warn "Service Registry health check timed out. Checking container logs..."
        ${COMPOSE_CMD} logs --tail=20
        exit 1
    fi

    log_success "Environment Started Successfully!"
    show_status
}

show_status() {
    log_info "Fetching Active Services & Devices from Registry (${REGISTRY_URL}/v1/services)..."
    echo -e "${CYAN}----------------------------------------------------------------------${NC}"
    if curl -s "${REGISTRY_URL}/v1/services" | grep -q '"success"'; then
        curl -s "${REGISTRY_URL}/v1/services"
    else
        log_warn "Unable to fetch services or no services currently registered."
    fi
    echo -e "\n${CYAN}----------------------------------------------------------------------${NC}"
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

test_resolve() {
    log_info "Resolving Active Target Endpoint for 'demo-analytics'..."
    curl -s "${REGISTRY_URL}/v1/resolve?service=demo-analytics" | grep -o '"port":[0-9]*' || true
}

stop_stack() {
    log_info "Stopping Docker Environment Stack..."
    cd "${INFRA_ROOT}"
    COMPOSE_CMD=$(get_compose_cmd)
    ${COMPOSE_CMD} down
    log_success "Docker environment stopped."
}

usage() {
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "${GREEN} Service Discovery & Dev/Stable Failover Runner ${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start            Build and start Docker Service Registry & Gateway"
    echo "  status           List all registered services & health states"
    echo "  register-demo    Register demo dev (8082) & stable (8081) devices"
    echo "  resolve          Query active target endpoint for traffic routing"
    echo "  stop             Stop all Docker containers"
    echo ""
}

case "${1:-}" in
    start)
        start_stack
        ;;
    status)
        show_status
        ;;
    register-demo)
        register_demo_devices
        ;;
    resolve)
        test_resolve
        ;;
    stop)
        stop_stack
        ;;
    *)
        usage
        ;;
esac
