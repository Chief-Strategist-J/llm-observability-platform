#!/bin/bash

set -e

BENCHMARK_MODE=${BENCHMARK_MODE:-false}
TEST_MODE=${TEST_MODE:-full}
USERS=${USERS:-3000}
SPAWN_RATE=${SPAWN_RATE:-1000}
RUN_TIME=${RUN_TIME:-3m}
LOCUST_WORKERS=${LOCUST_WORKERS:-2}

echo "=========================================="
echo "  Realistic Load Test — Target: 1M / 10m"
echo "=========================================="
echo "  USERS:           $USERS"
echo "  SPAWN_RATE:      $SPAWN_RATE"
echo "  RUN_TIME:        $RUN_TIME"
echo "  LOCUST_WORKERS:  $LOCUST_WORKERS"
echo ""

echo "Step 1: Tearing down any stale containers..."
docker-compose stop messaging-sdk messaging-sdk-2 2>/dev/null || true
docker-compose rm -f messaging-sdk messaging-sdk-2 2>/dev/null || true

echo ""
echo "Step 2: Starting database cluster..."
docker-compose up -d \
  postgres postgres-1 postgres-2 postgres-3 postgres-4 postgres-5 postgres-6 postgres-7 \
  mongodb mongodb-1 mongodb-2 mongodb-3 mongodb-4 mongodb-5 mongodb-6 mongodb-7 \
  redis

echo "Waiting 30s for databases to be healthy..."
sleep 30

echo ""
echo "Step 3: Starting messaging-sdk (server) container..."
docker-compose up -d --no-deps messaging-sdk

echo "Waiting 10s for messaging-sdk to be ready..."
sleep 10

echo ""
echo "Step 4: Starting realistic test server (multi-worker uvicorn)..."
docker exec messaging-sdk bash -c "
  cd /app && BATCH_SIZE=2000 MAX_LATENCY_MS=10 POSTGRES_MINCONN=20 POSTGRES_MAXCONN=100 \
  LOGICAL_SHARDS_PER_INSTANCE=8 ADAPTIVE_BATCHING=true UVICORN_WORKERS=3 \
  BENCHMARK_MODE=${BENCHMARK_MODE} TEST_MODE=${TEST_MODE} \
  python -m loadtests.test_server_realistic > /tmp/server.log 2>&1 &
  echo \$! > /tmp/server.pid
  echo 'Server started with PID:' \$(cat /tmp/server.pid)
"

echo "Waiting 12s for uvicorn workers to start..."
sleep 12

echo ""
echo "Step 5: Verifying server process is running..."
docker exec messaging-sdk bash -c "
  cat /tmp/server.pid | xargs -I{} python -c \"import os, sys; os.kill(int('{}'), 0); print('Server running')\" \
  || (echo '=== SERVER STARTUP FAILED ===' && cat /tmp/server.log && exit 1)
"

echo ""
echo "Step 6: Health check..."
docker exec messaging-sdk python -c "
import requests, time, sys
for i in range(15):
    try:
        r = requests.get('http://127.0.0.1:8001/health', timeout=3)
        print('Health:', r.json())
        sys.exit(0)
    except Exception as e:
        print(f'Attempt {i+1}/15 failed: {e}')
        time.sleep(2)
print('=== HEALTH CHECK FAILED ===')
sys.exit(1)
"

echo ""
echo "Step 7: Running Locust distributed load test ($LOCUST_WORKERS workers, $RUN_TIME)..."
docker exec messaging-sdk bash -c "
  locust -f loadtests/locustfile.py --master --headless \
    --host http://127.0.0.1:8001 \
    --users ${USERS} \
    --spawn-rate ${SPAWN_RATE} \
    --expect-workers ${LOCUST_WORKERS} \
    --expect-workers-max-wait 30 \
    --run-time ${RUN_TIME} \
    --html /tmp/realistic_test_report.html &
  MASTER_PID=\$!
  sleep 3
  for i in \$(seq 1 ${LOCUST_WORKERS}); do
    locust -f loadtests/locustfile.py --worker --master-host 127.0.0.1 &
    echo \"Worker \$i started\"
  done
  wait \$MASTER_PID
  python -c \"import os, signal
for line in open('/proc/\$\$/../children', 'r').readlines():
    try: os.kill(int(line), signal.SIGTERM)
    except: pass
\" 2>/dev/null || true
" || true

echo ""
echo "Step 8: Copying report to host..."
docker cp messaging-sdk:/tmp/realistic_test_report.html ./loadtests/realistic_test_report.html 2>/dev/null || \
  echo "WARNING: Could not copy report (test may have exited early)"

echo ""
echo "Step 9: Fetching final metrics..."
docker exec messaging-sdk python -c "
import requests
try:
    m = requests.get('http://127.0.0.1:8001/metrics', timeout=5).json()
    print('Total requests:  ', m.get('total_requests', 'N/A'))
    print('Request rate:    ', round(m.get('request_rate', 0), 1), 'RPS')
    print('Rejection rate:  ', round(m.get('rejection_rate', 0) * 100, 2), '%')
    lat = m.get('latency', {})
    print('Latency p50:     ', lat.get('p50_ms', 'N/A'), 'ms')
    print('Latency p99:     ', lat.get('p99_ms', 'N/A'), 'ms')
except Exception as e:
    print('Metrics unavailable:', e)
" 2>/dev/null || true

echo ""
echo "=========================================="
echo "  Test Complete!"
echo "=========================================="
echo "  Report: loadtests/realistic_test_report.html"
echo ""
