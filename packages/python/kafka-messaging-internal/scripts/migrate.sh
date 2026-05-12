#!/bin/bash
# Database migration script
# Runs migrations before application starts - MANDATORY according to migration rules

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MIGRATIONS_DIR="$PROJECT_ROOT/database/migrations"
SCHEMA_LOCK_FILE="$PROJECT_ROOT/database/schema.lock"

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

# Check if database is available
check_database() {
    log_info "Checking database connectivity..."
    
    # Use environment variables or defaults
    DB_DSN="${POSTGRES_DSN:-postgresql://localhost:5432/kafka_events}"
    
    if ! psql "$DB_DSN" -c "SELECT 1;" >/dev/null 2>&1; then
        log_error "Database is not accessible: $DB_DSN"
        exit 1
    fi
    
    log_info "Database connectivity verified"
}

# Get last applied migration
get_last_migration() {
    if [[ -f "$SCHEMA_LOCK_FILE" ]]; then
        local last_migration
        last_migration=$(cat "$SCHEMA_LOCK_FILE")
        echo "$last_migration"
    else
        echo "0"
    fi
}

# Apply a single migration
apply_migration() {
    local migration_file="$1"
    local migration_name
    migration_name=$(basename "$migration_file" .sql)
    
    log_info "Applying migration: $migration_name"
    
    # Check if migration file exists
    if [[ ! -f "$migration_file" ]]; then
        log_error "Migration file not found: $migration_file"
        exit 1
    fi
    
    # Get migration number from filename
    local migration_number
    migration_number=$(echo "$migration_name" | cut -d'_' -f1)
    
    # Apply migration
    if ! psql "$DB_DSN" -f "$migration_file"; then
        log_error "Failed to apply migration: $migration_name"
        exit 1
    fi
    
    # Update schema lock
    echo "$migration_number" > "$SCHEMA_LOCK_FILE"
    
    log_info "Migration applied successfully: $migration_name"
}

# Verify migration was applied
verify_migration() {
    local migration_number="$1"
    
    log_info "Verifying migration: $migration_number"
    
    # Basic verification - check if tables exist
    case "$migration_number" in
        "0001")
            if ! psql "$DB_DSN" -c "\dt kafka_events" >/dev/null 2>&1; then
                log_error "Verification failed: kafka_events table not found"
                exit 1
            fi
            
            if ! psql "$DB_DSN" -c "\dt consumer_offsets" >/dev/null 2>&1; then
                log_error "Verification failed: consumer_offsets table not found"
                exit 1
            fi
            ;;
    esac
    
    log_info "Migration verification passed: $migration_number"
}

# Run all pending migrations
run_migrations() {
    log_info "Starting database migration process"
    
    # Check migrations directory
    if [[ ! -d "$MIGRATIONS_DIR" ]]; then
        log_error "Migrations directory not found: $MIGRATIONS_DIR"
        exit 1
    fi
    
    # Get last applied migration
    local last_migration
    last_migration=$(get_last_migration)
    
    # Find and apply pending migrations
    local applied_any=false
    for migration_file in "$MIGRATIONS_DIR"/*.sql; do
        # Skip rollback files
        if [[ "$migration_file" == *.rollback.sql ]]; then
            continue
        fi
        
        local migration_name
        migration_name=$(basename "$migration_file" .sql)
        local migration_number
        migration_number=$(echo "$migration_name" | cut -d'_' -f1)
        
        # Apply if migration is newer than last applied
        if [[ "$migration_number" > "$last_migration" ]]; then
            apply_migration "$migration_file"
            verify_migration "$migration_number"
            applied_any=true
        fi
    done
    
    if [[ "$applied_any" == "false" ]]; then
        log_info "No pending migrations to apply"
    fi
    
    log_info "Migration process completed successfully"
}

# Rollback last migration
rollback_last() {
    log_warn "Rolling back last migration..."
    
    local last_migration
    last_migration=$(get_last_migration)
    
    if [[ "$last_migration" == "0" ]]; then
        log_error "No migrations to rollback"
        exit 1
    fi
    
    # Find rollback file
    local rollback_file
    rollback_file="$MIGRATIONS_DIR/${last_migration}.rollback.sql"
    
    if [[ ! -f "$rollback_file" ]]; then
        log_error "Rollback file not found: $rollback_file"
        exit 1
    fi
    
    # Apply rollback
    if ! psql "$DB_DSN" -f "$rollback_file"; then
        log_error "Failed to apply rollback: $rollback_file"
        exit 1
    fi
    
    # Update schema lock to previous migration
    local prev_migration
    prev_migration=$((last_migration - 1))
    if [[ "$prev_migration" -lt "1" ]]; then
        prev_migration="0"
    fi
    
    echo "$prev_migration" > "$SCHEMA_LOCK_FILE"
    
    log_info "Rollback completed successfully"
}

# Show migration status
show_status() {
    log_info "Migration Status:"
    echo "=================="
    
    local last_migration
    last_migration=$(get_last_migration)
    echo "Last Applied Migration: $last_migration"
    
    echo ""
    echo "Available Migrations:"
    for migration_file in "$MIGRATIONS_DIR"/*.sql; do
        if [[ "$migration_file" == *.rollback.sql ]]; then
            continue
        fi
        
        local migration_name
        migration_name=$(basename "$migration_file" .sql)
        local migration_number
        migration_number=$(echo "$migration_name" | cut -d'_' -f1)
        
        if [[ "$migration_number" > "$last_migration" ]]; then
            echo "  [PENDING] $migration_name"
        else
            echo "  [APPLIED]  $migration_name"
        fi
    done
    
    echo "=================="
}

# Main script logic
main() {
    case "${1:-run}" in
        "run")
            check_database
            run_migrations
            ;;
        "rollback")
            check_database
            rollback_last
            ;;
        "status")
            show_status
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [run|rollback|status]"
            echo ""
            echo "Commands:"
            echo "  run      - Run all pending migrations (default)"
            echo "  rollback  - Rollback the last applied migration"
            echo "  status   - Show migration status"
            echo "  help     - Show this help message"
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
