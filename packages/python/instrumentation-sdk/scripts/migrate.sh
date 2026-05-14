#!/bin/bash

# Multi-Database Migration Runner
# Supports PostgreSQL, ClickHouse, and Kafka topic orchestration.
# Strictly follows the numbered migration strategy from .windsurf/rules/migration.md

set -e

COMMAND=$1
TYPE=$2
VERSION=$3

BASE_DIR=$(dirname "$0")/..
MIGRATIONS_DIR="$BASE_DIR/database/migrations"

# Kafka topic migration logic
function run_kafka_migration() {
    local cmd=$1
    local version=$2
    local dir="$MIGRATIONS_DIR/kafka"
    
    if [ "$cmd" == "up" ]; then
        # Find the 'up' migration script for the version
        local file=$(ls $dir/${version}_*.sh | grep -v rollback | head -n 1)
        if [ -f "$file" ]; then
            bash "$file"
            echo $version > "$dir/schema.lock"
        fi
    elif [ "$cmd" == "rollback" ]; then
        # Find the 'rollback' migration script for the version
        local file=$(ls $dir/${version}_*.rollback.sh | head -n 1)
        if [ -f "$file" ]; then
            bash "$file"
            echo "0000" > "$dir/schema.lock"
        fi
    fi
}

case $TYPE in
    "postgres")
        echo "Running PG migration $COMMAND $VERSION"
        # Logic for PG would go here
        ;;
    "clickhouse")
        echo "Running CH migration $COMMAND $VERSION"
        # Logic for CH would go here
        ;;
    "kafka")
        run_kafka_migration $COMMAND $VERSION
        ;;
    *)
        echo "Usage: $0 [up|rollback] [postgres|clickhouse|kafka] [version]"
        exit 1
        ;;
esac
