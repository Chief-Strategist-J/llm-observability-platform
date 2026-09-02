#!/usr/bin/env bash

# ==============================================================================
# Dynamic Service Discovery & Traefik Reconciler Control Script
# Package: packages/configs/llm-obs-infra
# ==============================================================================

set -euo pipefail

# Color Codes for Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Determine Script & Repo Root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

REGISTRY_URL="http://localhost:31426"
TRAEFIK_DASHBOARD_URL="http://localhost:31411"

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

    log_info "Starting Service Discovery Registry & Traefik Gateway containers in Docker..."
    cd "${INFRA_ROOT}"
    COMPOSE_CMD=$(get_compose_cmd)
    
    ${COMPOSE_CMD} up -d --build llmobs-service-registry llmobs-traefik
    
    log_info "Waiting for Dynamic Service Registry to become healthy on port 31426..."
    local retries=15
    while [ $retries -gt 0 ]; do
        if curl -s "${REGISTRY_URL}/health" | grep -q '"status"'; then
            log_success "Dynamic Service Registry is ONLINE at ${REGISTRY_URL}"
            break
        fi
        sleep 1
        ((retries--))
    done

    if [ $retries -eq 0 ]; then
        log_warn "Service Registry health check timed out. Container logs:"
        ${COMPOSE_CMD} logs --tail=20 llmobs-service-registry
        exit 1
    fi

    log_success "Dynamic Service Discovery & Traefik Stack Running!"
    show_status
}

show_status() {
    log_info "Fetching Active Services from Dynamic Registry (${REGISTRY_URL}/v1/services)..."
    echo -e "${CYAN}----------------------------------------------------------------------${NC}"
    if curl -s "${REGISTRY_URL}/v1/services" | grep -q '"success"'; then
        curl -s "${REGISTRY_URL}/v1/services" | tr -d '\r'
    else
        log_warn "Unable to fetch services or registry is offline."
    fi
    echo -e "\n${CYAN}----------------------------------------------------------------------${NC}"
}

show_dynamic_traefik_config() {
    log_info "Reading Dynamically Reconciled Traefik Configuration..."
    echo -e "${MAGENTA}----------------------------------------------------------------------${NC}"
    if [ -d "${INFRA_ROOT}/config/traefik/dynamic" ]; then
        ls -la "${INFRA_ROOT}/config/traefik/dynamic"
        if [ -f "${INFRA_ROOT}/config/traefik/dynamic/discovery.yml" ]; then
            cat "${INFRA_ROOT}/config/traefik/dynamic/discovery.yml"
        fi
    fi

    # Check container generated config if running in docker
    cd "${INFRA_ROOT}"
    COMPOSE_CMD=$(get_compose_cmd)
    ${COMPOSE_CMD} exec -T llmobs-service-registry cat /etc/traefik/dynamic/discovery.yml 2>/dev/null || true
    echo -e "\n${MAGENTA}----------------------------------------------------------------------${NC}"
}

search_service() {
    local target_svc="${1:-}"
    if [ -z "$target_svc" ]; then
        log_error "Please specify a service name to search (e.g. $0 search clickhouse)"
        exit 1
    fi

    log_info "Searching and resolving dynamic endpoint for service '${target_svc}'..."
    echo -e "${CYAN}----------------------------------------------------------------------${NC}"
    curl -s "${REGISTRY_URL}/v1/resolve?service=${target_svc}"
    echo -e "\n${CYAN}----------------------------------------------------------------------${NC}"
}

register_dynamic_service() {
    local name="${1:-custom-service}"
    local port="${2:-8080}"
    local host="${3:-localhost}"

    log_info "Dynamically Registering Service '${name}' on ${host}:${port}..."
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
    log_success "Registered service '${name}'. Traefik exporter triggered atomic reconciliation!"
    search_service "${name}"
    show_dynamic_traefik_config
}

stop_stack() {
    log_info "Stopping Service Discovery & Traefik Containers..."
    cd "${INFRA_ROOT}"
    COMPOSE_CMD=$(get_compose_cmd)
    ${COMPOSE_CMD} stop llmobs-service-registry llmobs-traefik
    log_success "Containers stopped."
}

usage() {
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "${GREEN} Dynamic Service Discovery & Traefik Reconciler ${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start                           Build & start Service Registry + Traefik Gateway"
    echo "  status                          List all active services in memory"
    echo "  search <name>                   Search & resolve dynamic endpoint (e.g. clickhouse, redis)"
    echo "  register-dynamic <name> <port>  Register service dynamically & trigger Traefik sync"
    echo "  traefik-config                  Display live generated Traefik discovery.yml config"
    echo "  stop                            Stop Service Registry & Traefik containers"
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
    register-dynamic)
        register_dynamic_service "${2:-}" "${3:-8080}" "${4:-localhost}"
        ;;
    traefik-config)
        show_dynamic_traefik_config
        ;;
    stop)
        stop_stack
        ;;
    *)
        usage
        ;;
esac
