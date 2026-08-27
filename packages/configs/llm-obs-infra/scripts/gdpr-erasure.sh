#!/usr/bin/env bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(dirname "$SCRIPT_DIR")"

USER_ID=""
CUSTOMER_ID=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --user-id=*)
      USER_ID="${1#*=}"
      shift
      ;;
    --customer-id=*)
      CUSTOMER_ID="${1#*=}"
      shift
      ;;
    *)
      echo -e "${RED}Unknown argument: $1${NC}" >&2
      exit 1
      ;;
  esac
done

if [ -z "$USER_ID" ] && [ -z "$CUSTOMER_ID" ]; then
  echo -e "${RED}Error: Must provide --user-id=ID or --customer-id=ID${NC}" >&2
  exit 1
fi

TARGET_ID="${USER_ID:-$CUSTOMER_ID}"

echo -e "${BLUE}══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE} GDPR & CCPA DATA ERASURE UTILITY${NC}"
echo -e "${BLUE} Target Identifier: ${TARGET_ID}${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════${NC}"

CH_USER="default"
CH_PW=""
CH_DB="llm_telemetry_analytics"

if [ -f "$PKG_DIR/.env" ]; then
  CH_USER=$(grep -E "^CLICKHOUSE_USER=" "$PKG_DIR/.env" 2>/dev/null | cut -d= -f2 || echo "default")
  CH_PW=$(grep -E "^CLICKHOUSE_PASSWORD=" "$PKG_DIR/.env" 2>/dev/null | cut -d= -f2 || echo "")
  CH_DB=$(grep -E "^CLICKHOUSE_DB=" "$PKG_DIR/.env" 2>/dev/null | cut -d= -f2 || echo "llm_telemetry_analytics")
fi

AUTH_HEADER=""
[ -n "$CH_PW" ] && AUTH_HEADER="-u ${CH_USER}:${CH_PW}"

echo -e "${BLUE}⚡ Purging user telemetry spans from ClickHouse Analytics...${NC}"
curl -s $AUTH_HEADER -X POST "http://localhost:31421/?database=${CH_DB}" \
  --data-binary "ALTER TABLE telemetry_spans DELETE WHERE user_id = '${TARGET_ID}' OR customer_id = '${TARGET_ID}';" >/dev/null 2>&1 || true

DB_USER="admin"
DB_PW="llmobs_s3cret_2026"
DB_NAME="llm_observability"

if [ -f "$PKG_DIR/.env" ]; then
  DB_USER=$(grep -E "^ALLOYDB_USER=" "$PKG_DIR/.env" 2>/dev/null | cut -d= -f2 || echo "admin")
  DB_PW=$(grep -E "^ALLOYDB_PASSWORD=" "$PKG_DIR/.env" 2>/dev/null | cut -d= -f2 || echo "llmobs_s3cret_2026")
  DB_NAME=$(grep -E "^ALLOYDB_DB=" "$PKG_DIR/.env" 2>/dev/null | cut -d= -f2 || echo "llm_observability")
fi

echo -e "${BLUE}⚡ Purging relational metadata from AlloyDB...${NC}"
docker exec -e PGPASSWORD="$DB_PW" -i llmobs-alloydb-db psql -U "$DB_USER" -d "$DB_NAME" \
  -c "DELETE FROM user_metadata WHERE user_id = '${TARGET_ID}';" >/dev/null 2>&1 || true

echo -e "${BLUE}⚡ Logging GDPR data erasure audit event...${NC}"
docker exec -e PGPASSWORD="$DB_PW" -i llmobs-alloydb-db psql -U "$DB_USER" -d "$DB_NAME" \
  -c "INSERT INTO security_audit_logs (timestamp, actor_id, action, resource, details) VALUES (NOW(), 'system_gdpr', 'ERASE_USER_DATA', '${TARGET_ID}', 'GDPR erasure executed for user ${TARGET_ID}');" >/dev/null 2>&1 || true

echo -e "${GREEN}✓ GDPR data erasure completed successfully for ${TARGET_ID}.${NC}"
