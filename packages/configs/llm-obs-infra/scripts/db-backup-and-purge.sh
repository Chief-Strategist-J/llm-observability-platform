#!/usr/bin/env bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

get_script_dir() {
  cd "$(dirname "${BASH_SOURCE[0]}")" && pwd
}

get_pkg_dir() {
  local script_dir=$1
  dirname "$script_dir"
}

get_backup_dir() {
  local pkg_dir=$1
  echo "$pkg_dir/backups"
}

ensure_backup_dir() {
  local backup_dir=$1
  mkdir -p "$backup_dir"
}

get_timestamp() {
  date +"%Y%m%d_%H%M%S"
}

backup_alloydb() {
  local backup_dir=$1
  local ts=$2
  local target_file="$backup_dir/alloydb_dump_${ts}.sql"

  if docker ps --format '{{.Names}}' | grep -q "^llmobs-alloydb-db$"; then
    echo -e "${BLUE}📦 Dumping AlloyDB PostgreSQL database...${NC}"
    docker exec -t llmobs-alloydb-db pg_dumpall -U admin > "$target_file" 2>/dev/null || true
    if [ -s "$target_file" ]; then
      echo -e "${GREEN}✓ AlloyDB backup saved to: ${target_file}${NC}"
    else
      rm -f "$target_file"
      echo -e "${YELLOW}⚠️ AlloyDB dump returned empty file.${NC}"
    fi
  else
    echo -e "${YELLOW}⚠️ Container llmobs-alloydb-db is not running, skipping database dump.${NC}"
  fi
}

backup_clickhouse() {
  local backup_dir=$1
  local ts=$2
  local target_file="$backup_dir/clickhouse_schema_${ts}.sql"

  if docker ps --format '{{.Names}}' | grep -q "^llmobs-clickhouse-analytics$"; then
    echo -e "${BLUE}📦 Dumping ClickHouse schema...${NC}"
    docker exec -t llmobs-clickhouse-analytics clickhouse-client --query "SHOW CREATE DATABASE llm_telemetry_analytics" > "$target_file" 2>/dev/null || true
    if [ -s "$target_file" ]; then
      echo -e "${GREEN}✓ ClickHouse backup saved to: ${target_file}${NC}"
    else
      rm -f "$target_file"
      echo -e "${YELLOW}⚠️ ClickHouse dump returned empty file.${NC}"
    fi
  else
    echo -e "${YELLOW}⚠️ Container llmobs-clickhouse-analytics is not running, skipping schema dump.${NC}"
  fi
}

purge_database_volumes() {
  echo -e "${YELLOW}⚡ Stopping stack and purging database volumes...${NC}"
  local compose_file=$1
  local bin=$2

  $bin -f "$compose_file" down -v
  echo -e "${GREEN}✓ Database volumes deleted cleanly.${NC}"
}

main() {
  local script_dir
  script_dir=$(get_script_dir)

  local pkg_dir
  pkg_dir=$(get_pkg_dir "$script_dir")

  local compose_file="$pkg_dir/docker-compose.yml"
  local backup_dir
  backup_dir=$(get_backup_dir "$pkg_dir")

  ensure_backup_dir "$backup_dir"

  local ts
  ts=$(get_timestamp)

  local bin
  bin="docker compose"
  if ! docker compose version >/dev/null 2>&1; then
    bin="docker-compose"
  fi

  backup_alloydb "$backup_dir" "$ts"
  backup_clickhouse "$backup_dir" "$ts"
  purge_database_volumes "$compose_file" "$bin"
}

main "$@"
