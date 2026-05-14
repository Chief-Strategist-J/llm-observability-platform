#!/bin/bash
set -e

# Usage: ./scripts/migrate.sh [up|rollback] [clickhouse|postgres|kafka] [version]

COMMAND=${1:-up}
DB_TYPE=${2:-postgres}
VERSION=${3:-0001}

# Container names
PG_CONTAINER="docker-postgres-1"
CH_CONTAINER="docker-clickhouse-1"
KAFKA_CONTAINER="docker-kafka-1"

DB_DIR="database/migrations"

case "$DB_TYPE" in
  postgres)
    MIGRATION_FILE="$DB_DIR/postgres/${VERSION}_init.sql"
    ROLLBACK_FILE="$DB_DIR/postgres/${VERSION}_init.rollback.sql"
    
    if [ "$COMMAND" == "up" ]; then
        echo "Applying Postgres migration $VERSION..."
        docker exec -i "$PG_CONTAINER" psql -U admin -d llm_observability < "$MIGRATION_FILE"
    else
        echo "Rolling back Postgres migration $VERSION..."
        docker exec -i "$PG_CONTAINER" psql -U admin -d llm_observability < "$ROLLBACK_FILE"
    fi
    ;;
    
  clickhouse)
    MIGRATION_FILE="$DB_DIR/clickhouse/${VERSION}_init.sql"
    ROLLBACK_FILE="$DB_DIR/clickhouse/${VERSION}_init.rollback.sql"

    if [ "$COMMAND" == "up" ]; then
        echo "Applying ClickHouse migration $VERSION..."
        docker exec -i "$CH_CONTAINER" clickhouse-client --database default < "$MIGRATION_FILE"
    else
        echo "Rolling back ClickHouse migration $VERSION..."
        docker exec -i "$CH_CONTAINER" clickhouse-client --database default < "$ROLLBACK_FILE"
    fi
    ;;
    
  kafka)
    SUFFIX=""
    if [ "$COMMAND" == "rollback" ]; then
        SUFFIX=".rollback"
    fi
    MIGRATION_FILE="$DB_DIR/kafka/${VERSION}_init${SUFFIX}.sh"
    
    echo "Executing Kafka migration $VERSION ($COMMAND)..."
    if [ -f "$MIGRATION_FILE" ]; then
        bash "$MIGRATION_FILE"
    else
        echo "Migration file not found: $MIGRATION_FILE"
        exit 1
    fi
    ;;
    
  *)
    echo "Unknown database type: $DB_TYPE"
    exit 1
    ;;
esac

echo "Migration $COMMAND for $DB_TYPE ($VERSION) completed."
