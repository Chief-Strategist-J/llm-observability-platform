#!/bin/bash

set -e

COMMAND=$1
TYPE=$2
VERSION=$3

BASE_DIR=$(dirname "$0")/..
MIGRATIONS_DIR="$BASE_DIR/database/migrations"

function run_kafka_migration() {
    local cmd=$1
    local version=$2
    local dir="$MIGRATIONS_DIR/kafka"
    
    if [ "$cmd" == "up" ]; then
        local file=$(ls $dir/${version}_*.sh | grep -v rollback | head -n 1)
        if [ -f "$file" ]; then
            bash "$file"
            echo $version > "$dir/schema.lock"
        fi
    elif [ "$cmd" == "rollback" ]; then
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
        ;;
    "clickhouse")
        echo "Running CH migration $COMMAND $VERSION"
        ;;
    "kafka")
        run_kafka_migration $COMMAND $VERSION
        ;;
    *)
        echo "Usage: $0 [up|rollback] [postgres|clickhouse|kafka] [version]"
        exit 1
        ;;
esac
