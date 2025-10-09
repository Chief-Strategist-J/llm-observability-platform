#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.neo4j-memory.yml"
ENV_FILE="$SCRIPT_DIR/.env"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi

    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available"
        exit 1
    fi

    print_success "Docker is available"
}

check_env() {
    if [ ! -f "$ENV_FILE" ]; then
        print_error ".env file not found at $ENV_FILE"
        exit 1
    fi
    print_success ".env file found"
}

start_services() {
    print_header "Starting Neo4j MCP Services"

    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

    print_info "Waiting for services..."
    sleep 10

    show_status
    show_urls
}

stop_services() {
    print_header "Stopping Neo4j MCP Services"

    docker compose -f "$COMPOSE_FILE" down

    print_success "Services stopped"
}

restart_services() {
    print_header "Restarting Neo4j MCP Services"

    docker compose -f "$COMPOSE_FILE" restart

    print_success "Services restarted"
    show_status
}

show_status() {
    print_header "Service Status"

    docker compose -f "$COMPOSE_FILE" ps
}

show_logs() {
    local service=$1

    if [ -z "$service" ]; then
        print_header "All Service Logs"
        docker compose -f "$COMPOSE_FILE" logs -f --tail=100
    else
        case $service in
            neo4j)
                print_header "Neo4j Database Logs"
                docker logs -f neo4j-memory
                ;;
            memory)
                print_header "Memory MCP Server Logs"
                docker logs -f neo4j-mcp-memory
                ;;
            cypher)
                print_header "Cypher MCP Server Logs"
                docker logs -f neo4j-mcp-cypher
                ;;
            data-modeling)
                print_header "Data Modeling MCP Server Logs"
                docker logs -f neo4j-mcp-data-modeling
                ;;
            *)
                print_error "Unknown service: $service"
                print_info "Valid services: neo4j, memory, cypher, data-modeling"
                exit 1
                ;;
        esac
    fi
}

clear_all() {
    print_header "CLEAR ALL DATA"

    read -p "Delete all Neo4j data? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_info "Cancelled"
        exit 0
    fi

    print_warning "Stopping services..."
    docker compose -f "$COMPOSE_FILE" down

    print_warning "Removing volumes..."
    docker volume rm mcp-neo4j-memory_neo4j_data mcp-neo4j-memory_neo4j_logs mcp-neo4j-memory_neo4j_import mcp-neo4j-memory_neo4j_plugins 2>/dev/null || true

    print_success "Data cleared"
}

diagnose() {
    print_header "Diagnostics"

    echo -e "\n${CYAN}Container Status:${NC}"
    docker compose -f "$COMPOSE_FILE" ps

    echo -e "\n${CYAN}Neo4j HTTP (7475):${NC}"
    curl -sf http://localhost:7475 > /dev/null 2>&1 && print_success "Accessible" || print_error "Not accessible"

    echo -e "\n${CYAN}Neo4j Bolt (7688):${NC}"
    nc -z localhost 7688 2>/dev/null && print_success "Accessible" || print_error "Not accessible"

    echo -e "\n${CYAN}MCP Memory Server (8000):${NC}"
    curl -sf http://localhost:8000/mcp/ > /dev/null 2>&1 && print_success "Accessible" || print_error "Not accessible"

    echo -e "\n${CYAN}MCP Cypher Server (8001):${NC}"
    curl -sf http://localhost:8001/mcp/ > /dev/null 2>&1 && print_success "Accessible" || print_error "Not accessible"

    echo -e "\n${CYAN}MCP Data Modeling Server (8002):${NC}"
    curl -sf http://localhost:8002/mcp/ > /dev/null 2>&1 && print_success "Accessible" || print_error "Not accessible"

    echo -e "\n${CYAN}Recent Logs:${NC}"
    docker compose -f "$COMPOSE_FILE" logs --tail=5
}

show_urls() {
    print_header "Access URLs"

    echo -e "${CYAN}Neo4j Browser:${NC}           http://localhost:7475"
    echo -e "${CYAN}Neo4j Bolt:${NC}              bolt://localhost:7688"
    echo -e "${CYAN}MCP Memory Server:${NC}       http://localhost:8000/mcp/"
    echo -e "${CYAN}MCP Cypher Server:${NC}       http://localhost:8001/mcp/"
    echo -e "${CYAN}MCP Data Modeling:${NC}       http://localhost:8002/mcp/"
    echo -e "${CYAN}Username:${NC}                neo4j"
    echo -e "${CYAN}Password:${NC}                Scaibu@123"
    echo ""
}

show_help() {
    cat << EOF
${CYAN}Neo4j MCP Services Management${NC}

${YELLOW}Commands:${NC}
  start              Start all services
  stop               Stop all services
  restart            Restart all services
  status             Show service status
  logs               Show all logs
  logs [service]     Show logs for specific service
                     Services: neo4j, memory, cypher, data-modeling
  clear              Clear all data
  diagnose           Run diagnostics
  urls               Show access URLs
  help               Show this help

${YELLOW}Examples:${NC}
  ./deploy.sh start
  ./deploy.sh logs memory
  ./deploy.sh diagnose
EOF
}

main() {
    check_docker

    case "${1:-help}" in
        start)
            check_env
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        clear)
            clear_all
            ;;
        diagnose)
            diagnose
            ;;
        urls)
            show_urls
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
