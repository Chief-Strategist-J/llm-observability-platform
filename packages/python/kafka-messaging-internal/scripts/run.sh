#!/bin/bash
# Application startup script - runs migrations first then starts app

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
check_env_file() {
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        log_warn ".env file not found, using environment variables"
        if [[ ! -f "$PROJECT_ROOT/.env.example" ]]; then
            log_error ".env.example file not found"
            exit 1
        fi
        log_info "Copy .env.example to .env and configure your environment"
        exit 1
    fi
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    if ! "$SCRIPT_DIR/migrate.sh" run; then
        log_error "Database migration failed"
        exit 1
    fi
    
    log_info "Database migrations completed successfully"
}

# Start the application
start_application() {
    log_info "Starting Kafka Messaging Internal API..."
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Set PYTHONPATH
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    
    # Run the application
    if command -v uvicorn >/dev/null 2>&1; then
        uvicorn kafka_messaging_internal.main:main \
            --host "${API_HOST:-0.0.0.0}" \
            --port "${API_PORT:-8000}" \
            --reload "${API_RELOAD:-false}" \
            --log-level "${LOG_LEVEL:-info}"
    else
        log_error "uvicorn not found. Install with: pip install uvicorn"
        exit 1
    fi
}

# Main function
main() {
    case "${1:-start}" in
        "start")
            check_env_file
            run_migrations
            start_application
            ;;
        "migrate")
            "$SCRIPT_DIR/migrate.sh" run
            ;;
        "migrate-rollback")
            "$SCRIPT_DIR/migrate.sh" rollback
            ;;
        "migrate-status")
            "$SCRIPT_DIR/migrate.sh" status
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [start|migrate|migrate-rollback|migrate-status|help]"
            echo ""
            echo "Commands:"
            echo "  start           - Run migrations and start application (default)"
            echo "  migrate         - Run database migrations only"
            echo "  migrate-rollback - Rollback last migration"
            echo "  migrate-status  - Show migration status"
            echo "  help            - Show this help message"
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
