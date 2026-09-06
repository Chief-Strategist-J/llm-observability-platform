#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATIONS_DIR="$(cd "$SCRIPT_DIR/../database/migrations" && pwd)"

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-quality_engine_db}"

export PGPASSWORD="$POSTGRES_PASSWORD"

echo "[quality-engine] Running migrations against $POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB..."

for sql_file in "$MIGRATIONS_DIR"/*.sql; do
    # Skip rollback files
    if [[ "$sql_file" == *".rollback.sql" ]]; then
        continue
    fi
    echo "  -> Applying: $(basename "$sql_file")"
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$sql_file"
done

echo "[quality-engine] Migrations complete."
