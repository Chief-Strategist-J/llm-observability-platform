#!/bin/bash

set -e

echo "=================================="
echo "Basic Load Test - test_server.py"
echo "=================================="

echo "Step 1: Starting messaging-sdk container (no deps)..."
docker-compose up -d --no-deps messaging-sdk

echo "Waiting for messaging-sdk to be ready..."
sleep 5

echo "Step 2: Starting basic test server..."
docker exec messaging-sdk bash -c "
  cd /app && python -m loadtests.test_server > /tmp/basic_server.log 2>&1 &
  echo \$! > /tmp/basic_server.pid
"

echo "Waiting for test server to start..."
sleep 5

echo "Step 3: Verifying server process is running..."
docker exec messaging-sdk bash -c "
  kill -0 \$(cat /tmp/basic_server.pid) 2>/dev/null && echo 'Server running' || (cat /tmp/basic_server.log && exit 1)
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

echo ""
echo "Step 5: Running Locust load test..."
echo "Configuration: 1000 users, 100 spawn rate, 1 minute duration"
echo ""

docker exec messaging-sdk locust \
  -f loadtests/locustfile.py \
  --headless \
  --host http://localhost:8001 \
  --users 1000 \
  --spawn-rate 100 \
  --run-time 1m \
  --html /tmp/basic_test_report.html || true

echo ""
echo "Step 6: Copying report to host..."
docker cp messaging-sdk:/tmp/basic_test_report.html ./loadtests/basic_test_report.html

echo ""
echo "Step 7: Stopping test server..."
docker exec messaging-sdk python -c "import os; os.system('pkill -f test_server')" || true

echo ""
echo "=================================="
echo "Test Complete!"
echo "=================================="
echo "Report saved to: loadtests/basic_test_report.html"
echo ""
