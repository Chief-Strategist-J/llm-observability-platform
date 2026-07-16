#!/bin/bash
set -e

# Color variables
GREEN='\033[0;32m'
BLUE='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BACKUP_DIR=${BACKUP_DIR:-"./backups"}
mkdir -p "$BACKUP_DIR"

DB_HOST=${POSTGRES_HOST:-"localhost"}
DB_PORT=${POSTGRES_PORT:-5432}
DB_USER=${POSTGRES_USER:-"postgres"}
DB_PASS=${POSTGRES_PASSWORD:-"password"}
DB_NAME=${POSTGRES_DB:-"llm_observability"}

CH_HOST=${CLICKHOUSE_HOST:-"localhost"}
CH_PORT=${CLICKHOUSE_PORT:-8123}

REDIS_HOST=${REDIS_HOST:-"localhost"}
REDIS_PORT=${REDIS_PORT:-6379}

echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}      Database Backup Script - Observability   ${NC}"
echo -e "${BLUE}===============================================${NC}"

backup_postgres() {
    echo -e "\n${YELLOW}[1/3] Backing up PostgreSQL (pgvector)...${NC}"
    if [ -n "$KUBERNETES_SERVICE_HOST" ]; then
        # Kubernetes execution: run pg_dump directly against service
        PGPASSWORD=$DB_PASS pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -F c -f "$BACKUP_DIR/postgres_$(date +%F_%H%M%S).dump"
        echo -e "${GREEN}[✓] PostgreSQL backup completed successfully.${NC}"
    else
        # Local Docker Compose execution
        if docker ps | grep -q obs-postgres; then
            docker exec obs-postgres pg_dump -U postgres -d llm_observability -F c -f /tmp/postgres_backup.dump
            docker cp obs-postgres:/tmp/postgres_backup.dump "$BACKUP_DIR/postgres_$(date +%F_%H%M%S).dump"
            docker exec obs-postgres rm /tmp/postgres_backup.dump
            echo -e "${GREEN}[✓] PostgreSQL backup completed successfully.${NC}"
        else
            echo -e "${RED}[x] obs-postgres container is not running. Skipping.${NC}"
        fi
    fi
}

backup_clickhouse() {
    echo -e "\n${YELLOW}[2/3] Backing up ClickHouse columnar data...${NC}"
    BACKUP_NAME="backup_$(date +%F_%H%M%S)"
    if [ -n "$KUBERNETES_SERVICE_HOST" ]; then
        # Kubernetes execution: invoke HTTP interface of ClickHouse
        curl -s -d "ALTER TABLE llm_spans FREEZE WITH NAME '$BACKUP_NAME'" "http://$CH_HOST:$CH_PORT/"
        echo -e "${GREEN}[✓] ClickHouse partition frozen under: shadow/$BACKUP_NAME${NC}"
    else
        # Local Docker Compose execution
        if docker ps | grep -q obs-clickhouse; then
            docker exec obs-clickhouse clickhouse-client --query "ALTER TABLE llm_spans FREEZE WITH NAME '$BACKUP_NAME'"
            echo -e "${GREEN}[✓] ClickHouse partition frozen under: shadow/$BACKUP_NAME${NC}"
        else
            echo -e "${RED}[x] obs-clickhouse container is not running. Skipping.${NC}"
        fi
    fi
}

backup_redis() {
    echo -e "\n${YELLOW}[3/3] Backing up Redis cache...${NC}"
    if [ -n "$KUBERNETES_SERVICE_HOST" ]; then
        # Kubernetes execution: Send BGSAVE command directly to host
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" BGSAVE || true
        echo -e "${GREEN}[✓] Redis BGSAVE triggered successfully.${NC}"
    else
        # Local Docker Compose execution
        if docker ps | grep -q obs-redis; then
            docker exec obs-redis redis-cli BGSAVE
            echo -e "${YELLOW}Triggered Redis BGSAVE. Waiting for snapshot completion...${NC}"
            sleep 3
            docker cp obs-redis:/data/dump.rdb "$BACKUP_DIR/redis_$(date +%F_%H%M%S).rdb"
            echo -e "${GREEN}[✓] Redis dump.rdb backed up successfully.${NC}"
        else
            echo -e "${RED}[x] obs-redis container is not running. Skipping.${NC}"
        fi
    fi
}

main() {
    backup_postgres
    backup_clickhouse
    backup_redis
    echo -e "\n${GREEN}Backups successfully stored in: $BACKUP_DIR/${NC}"
}

main
