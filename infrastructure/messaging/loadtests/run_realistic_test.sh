#!/bin/bash

set -e

BENCHMARK_MODE=${BENCHMARK_MODE:-false}
TEST_MODE=${TEST_MODE:-full}

echo "=================================="
echo "Realistic Load Test - 1M Requests"
echo "=================================="
echo "BENCHMARK_MODE: $BENCHMARK_MODE"
echo "TEST_MODE: $TEST_MODE"
echo ""

echo "Step 1: Starting all database instances..."
docker-compose up -d postgres postgres-1 postgres-2 postgres-3 postgres-4 postgres-5 postgres-6 postgres-7 mongodb mongodb-1 mongodb-2 mongodb-3 mongodb-4 mongodb-5 mongodb-6 mongodb-7 redis

echo "Waiting for databases to be healthy..."
sleep 30

echo "Step 2: Starting messaging-sdk container..."
docker-compose up -d --no-deps messaging-sdk

echo "Waiting for messaging-sdk to be ready..."
sleep 10

echo "Step 3: Starting realistic test server..."
docker exec messaging-sdk bash -c "
  cd /app && python -m loadtests.test_server_realistic > /tmp/server.log 2>&1 &
  echo \$! > /tmp/server.pid
"

echo "Waiting for test server to start..."
sleep 8

echo "Step 3.5: Verifying server process is running..."
docker exec messaging-sdk bash -c "
  kill -0 \$(cat /tmp/server.pid) 2>/dev/null && echo 'Server running' || (cat /tmp/server.log && exit 1)
"

echo "Step 4: Checking server health..."
docker exec messaging-sdk python -c "
import requests, time, sys
for i in range(10):
    try:
        r = requests.get('http://localhost:8001/health', timeout=2)
        print(r.json())
        sys.exit(0)
    except Exception as e:
        print(f'Attempt {i+1}/10 failed: {e}')
        time.sleep(2)
sys.exit(1)
"
docker exec messaging-sdk python -c "import requests; print(requests.get('http://localhost:8001/metrics').json())"

echo ""
echo "Step 5: Running Locust load test for 1M requests..."
echo "Configuration: 2000 users, 200 spawn rate, no wait time"
echo ""

docker exec messaging-sdk locust \
  -f loadtests/locustfile.py \
  --headless \
  --host http://localhost:8001 \
  --users 2000 \
  --spawn-rate 200 \
  --expect-workers-max-wait 10 \
  --html /tmp/realistic_test_report.html

echo ""
echo "Step 6: Copying report to host..."
docker cp messaging-sdk:/tmp/realistic_test_report.html ./loadtests/realistic_test_report.html

echo ""
echo "Step 7: Stopping test server..."
docker exec messaging-sdk python -c "import os; os.system('pkill -f test_server_realistic')" || true

echo ""
echo "=================================="
echo "Test Complete!"
echo "=================================="
echo "Report saved to: loadtests/realistic_test_report.html"
echo ""
echo "To view the report, open the HTML file in your browser."
