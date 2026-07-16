#!/bin/bash
set -e

# Color variables
GREEN='\033[0;32m'
BLUE='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DB_HOST=${POSTGRES_HOST:-"localhost"}
DB_PORT=${POSTGRES_PORT:-5432}
DB_USER=${POSTGRES_USER:-"postgres"}
DB_PASS=${POSTGRES_PASSWORD:-"password"}
DB_NAME=${POSTGRES_DB:-"llm_observability"}

CH_HOST=${CLICKHOUSE_HOST:-"localhost"}
CH_PORT=${CLICKHOUSE_PORT:-8123}

echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}      Automated Database Migrations Runner     ${NC}"
echo -e "${BLUE}===============================================${NC}"

# 1. Wait for PostgreSQL
echo -e "${YELLOW}Waiting for PostgreSQL ($DB_HOST:$DB_PORT) to be healthy...${NC}"
until PGPASSWORD=$DB_PASS psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "select 1" &> /dev/null; do
  sleep 2
done
echo -e "${GREEN}[✓] PostgreSQL is healthy.${NC}"

# 2. Wait for ClickHouse
echo -e "${YELLOW}Waiting for ClickHouse ($CH_HOST:$CH_PORT) to be healthy...${NC}"
until curl -s "http://$CH_HOST:$CH_PORT/ping" | grep -q "Ok"; do
  sleep 2
done
echo -e "${GREEN}[✓] ClickHouse is healthy.${NC}"

# 3. Apply PostgreSQL Migrations
echo -e "\n${YELLOW}Applying PostgreSQL migrations...${NC}"
if [ -d "/migrations" ]; then
  for file in /migrations/postgres-*.sql; do
    if [ -f "$file" ]; then
      echo -e "${BLUE}Running Postgres migration: $file...${NC}"
      PGPASSWORD=$DB_PASS psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$file"
    fi
  done
else
  MIGRATION_FILES=(
    "packages/python/instrumentation-sdk/database/migrations/postgres/0001_init.sql"
    "packages/python/quality-engine/database/migrations/0001_init.sql"
    "packages/python/quality-engine/database/migrations/0002_add_review_status.sql"
    "packages/python/forecast-worker/database/migrations/0001_init.sql"
    "packages/python/kafka-messaging-internal/database/migrations/0001_init.sql"
    "packages/python/queue-embedding-worker/database/migrations/0001_init.sql"
    "packages/python/alert-engine/database/migrations/0001_init.sql"
    "packages/python/budget-provisioner/database/migrations/0001_init.sql"
    "packages/python/temporal-ewma-worker/database/migrations/0001_init.sql"
    "packages/python/latency-baseline-worker/database/migrations/0001_init.sql"
    "packages/go/tracep/database/migrations/0001_init.sql"
  )

  for file in "${MIGRATION_FILES[@]}"; do
    if [ -f "$file" ]; then
      echo -e "${BLUE}Running Postgres migration: $file...${NC}"
      PGPASSWORD=$DB_PASS psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$file"
    else
      echo -e "${YELLOW}[!] Migration file not found: $file. Skipping.${NC}"
    fi
  done
fi
echo -e "${GREEN}[✓] All PostgreSQL migrations applied.${NC}"

# 4. Apply ClickHouse Migrations
echo -e "\n${YELLOW}Applying ClickHouse migrations...${NC}"
if [ -d "/migrations" ]; then
  for file in /migrations/clickhouse-*.sql; do
    if [ -f "$file" ]; then
      echo -e "${BLUE}Running ClickHouse migration: $file...${NC}"
      curl -s -d "$(cat "$file")" "http://$CH_HOST:$CH_PORT/"
    fi
  done
else
  CH_MIGRATION_FILES=(
    "packages/python/instrumentation-sdk/database/migrations/clickhouse/0001_init.sql"
  )

  for file in "${CH_MIGRATION_FILES[@]}"; do
    if [ -f "$file" ]; then
      echo -e "${BLUE}Running ClickHouse migration: $file...${NC}"
      curl -s -d "$(cat "$file")" "http://$CH_HOST:$CH_PORT/"
    else
      echo -e "${YELLOW}[!] Migration file not found: $file. Skipping.${NC}"
    fi
  done
fi
echo -e "${GREEN}[✓] All ClickHouse migrations applied.${NC}"

echo -e "\n${GREEN}Automated migrations completed successfully!${NC}"
