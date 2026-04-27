#!/bin/bash

set -e

echo "=================================="
echo "Realistic Load Test - 1M Requests"
echo "=================================="
echo ""

echo "Step 1: Starting all database instances..."
docker-compose up -d postgres postgres-1 postgres-2 postgres-3 mongodb mongodb-1 mongodb-2 mongodb-3

echo "Waiting for databases to be healthy..."
sleep 30

echo "Step 2: Starting messaging-sdk container..."
docker-compose up -d messaging-sdk

echo "Waiting for messaging-sdk to be ready..."
sleep 10

echo "Step 3: Starting realistic test server..."
docker exec -d messaging-sdk python loadtests/test_server_realistic.py

echo "Waiting for test server to start..."
sleep 5

echo "Step 4: Checking server health..."
docker exec messaging-sdk python -c "import requests; print(requests.get('http://localhost:8001/health').json())"

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
