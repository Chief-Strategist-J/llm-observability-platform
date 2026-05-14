#!/bin/bash
set -e

# Usage: ./scripts/migrate.sh [up|rollback] [clickhouse|postgres]

COMMAND=${1:-up}
DB_TYPE=${2:-postgres}

# Container names based on docker-compose.dev.yaml (which uses 'docker-' prefix by default in this env)
PG_CONTAINER="docker-postgres-1"
CH_CONTAINER="docker-clickhouse-1"

DB_DIR="database/migrations"

if [ "$DB_TYPE" == "postgres" ]; then
    MIGRATION_FILE="$DB_DIR/postgres/0001_init.sql"
    ROLLBACK_FILE="$DB_DIR/postgres/0001_init.rollback.sql"
    
    if [ "$COMMAND" == "up" ]; then
        echo "Applying Postgres migrations..."
        docker exec -i "$PG_CONTAINER" psql -U admin -d llm_observability < "$MIGRATION_FILE"
    else
        echo "Rolling back Postgres migrations..."
        docker exec -i "$PG_CONTAINER" psql -U admin -d llm_observability < "$ROLLBACK_FILE"
    fi
elif [ "$DB_TYPE" == "clickhouse" ]; then
    MIGRATION_FILE="$DB_DIR/clickhouse/0001_init.sql"
    ROLLBACK_FILE="$DB_DIR/clickhouse/0001_init.rollback.sql"

    if [ "$COMMAND" == "up" ]; then
        echo "Applying ClickHouse migrations..."
        docker exec -i "$CH_CONTAINER" clickhouse-client --database default < "$MIGRATION_FILE"
    else
        echo "Rolling back ClickHouse migrations..."
        docker exec -i "$CH_CONTAINER" clickhouse-client --database default < "$ROLLBACK_FILE"
    fi
else
    echo "Unknown database type: $DB_TYPE"
    exit 1
fi

echo "Migration $COMMAND for $DB_TYPE completed."
