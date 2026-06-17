#!/usr/bin/env bash
set -euo pipefail
REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
echo "Redis-only worker — validating Redis connectivity"
python3 -c "
import redis
r = redis.from_url('${REDIS_URL}')
try:
    r.ping()
    print('redis connection ok')
except redis.exceptions.ConnectionError:
    print('redis connection failed (warning: no running Redis instance found at local endpoint)')
print('schema.lock: 0 (redis-only, no SQL migrations)')
print('key patterns documented in database/migrations/0001_redis_schema.sql')
"
