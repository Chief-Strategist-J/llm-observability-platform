#!/usr/bin/env python3
import subprocess
import time
import urllib.request
import json
import os
import sys

# Configuration
ENDPOINT = "http://localhost:4318"
QUERY_ENDPOINT = "http://localhost:4319"
AUTH_TOKEN = "test-token-12345"

# Setup directories
python_dir = "/home/btpl-lap-22/live/obs/packages/python/tracep"
node_dir = "/home/btpl-lap-22/live/obs/packages/node/tracep"
go_dir = "/home/btpl-lap-22/live/obs/packages/go/tracep"

def run_cmd(cmd, cwd=None, env=None, check=True):
    print(f"Executing: {cmd}")
    # Inherit existing env and update
    current_env = os.environ.copy()
    if env:
        current_env.update(env)
    res = subprocess.run(cmd, shell=True, cwd=cwd, env=current_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and res.returncode != 0:
        print(f"Error executing {cmd}:\nStdout: {res.stdout}\nStderr: {res.stderr}")
        raise subprocess.CalledProcessError(res.returncode, cmd, res.stdout, res.stderr)
    return res

def query_trace(tid):
    req = urllib.request.Request(
        f"{QUERY_ENDPOINT}/traces/{tid}",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
    )
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode())
    except Exception as e:
        print(f"Failed to query trace {tid}: {e}")
        return None

def main():
    print("=== Starting live traceserver container ===")
    # Clean up existing container if any
    subprocess.run("docker rm -f traceserver-integration-test 2>/dev/null", shell=True)
    
    # Start container
    run_cmd(
        f"docker run -d --name traceserver-integration-test "
        f"-p 4318:4318 -p 4319:4319 "
        f"-e TRACE_TOKEN={AUTH_TOKEN} "
        f"-e DB_PATH=/app/data/traces.db "
        f"traceserver:test"
    )
    
    # Wait for server to start
    time.sleep(3)
    
    results = {}
    
    # Create directory for integration test scripts if not exists
    os.makedirs("/home/btpl-lap-22/live/obs/packages/go/tracep/tests/integration", exist_ok=True)
    
    try:
        # ==========================================
        # 1. Python SDK Integration
        # ==========================================
        print("\n=== Testing Python SDK ===")
        
        py_test_code = """
from tracep import Tracer
import time
t = Tracer("http://localhost:4318", "test-token-12345", "python-integration-service")
tid = t.start("py-live-test")
t.trace(tid, "PythonClass", "run_test", "step_1", "Hello from Python OTel SDK!")
t.end(tid, "ok")
t.close()
print(tid)
"""
        with open("/tmp/py_test.py", "w") as f:
            f.write(py_test_code.strip())
            
        py_tid = run_cmd(
            "python3 /tmp/py_test.py",
            env={"PYTHONPATH": os.path.join(python_dir, "src")}
        ).stdout.strip()
        print(f"Python Trace ID: {py_tid}")
        
        # Verify trace in SQLite/Query API
        time.sleep(1.5) # Allow exporter queue to flush
        trace_data = query_trace(py_tid)
        if trace_data and trace_data.get("name") == "py-live-test":
            print("Python Integration: SUCCESS")
            results["python"] = "PASS"
        else:
            print(f"Python Integration: FAILED (Trace data: {trace_data})")
            results["python"] = "FAIL"

        # ==========================================
        # 2. Node/JS SDK Integration
        # ==========================================
        print("\n=== Testing Node/JS SDK ===")
        # Compile TS if needed
        run_cmd("npm install --no-audit --no-fund", cwd=node_dir)
        run_cmd("npx tsc", cwd=node_dir)
        
        node_test_code = """
const { Tracer } = require('./dist/tracer.js');
async function run() {
  const t = new Tracer("http://localhost:4318", "test-token-12345", "node-integration-service");
  const tid = t.start("node-live-test");
  t.trace(tid, "NodeClass", "run_test", "step_1", "Hello from Node OTel SDK!");
  await t.end(tid, "ok");
  await t.close();
  console.log(tid);
}
run();
"""
        with open(os.path.join(node_dir, "node_test.cjs"), "w") as f:
            f.write(node_test_code.strip())
            
        node_tid = run_cmd("node node_test.cjs", cwd=node_dir).stdout.strip()
        print(f"Node Trace ID: {node_tid}")
        
        # Verify trace in SQLite/Query API
        time.sleep(1.5)
        trace_data = query_trace(node_tid)
        if trace_data and trace_data.get("name") == "node-live-test":
            print("Node Integration: SUCCESS")
            results["node"] = "PASS"
        else:
            print(f"Node Integration: FAILED (Trace data: {trace_data})")
            results["node"] = "FAIL"

        # ==========================================
        # 3. Go SDK Integration
        # ==========================================
        print("\n=== Testing Go SDK ===")
        # Run inside a docker container sharing network host to reach traceserver easily
        go_test_code = """
package main
import (
	"fmt"
	"github.com/llm-observability/platform/packages/go/tracep"
)
func main() {
	t, err := tracep.New("http://localhost:4318", "test-token-12345", "go-integration-service")
	if err != nil {
		panic(err)
	}
	tid := t.Start("go-live-test")
	t.Trace(tid, "GoClass", "run_test", "step_1", "Hello from Go OTel SDK!")
	t.End(tid, "ok")
	t.Close()
	fmt.Println(tid)
}
"""
        go_test_dir = os.path.join(go_dir, "tests/integration/go_test")
        os.makedirs(go_test_dir, exist_ok=True)
        with open(os.path.join(go_test_dir, "go_integration.go"), "w") as f:
            f.write(go_test_code.strip())
            
        go_tid = run_cmd(
            f"docker run --rm --network host -v {go_dir}:/app -w /app/tests/integration/go_test golang:1.21-alpine "
            f"go run go_integration.go"
        ).stdout.strip()
        print(f"Go Trace ID: {go_tid}")
        
        # Verify trace in SQLite/Query API
        time.sleep(1.5)
        trace_data = query_trace(go_tid)
        if trace_data and trace_data.get("name") == "go-live-test":
            print("Go Integration: SUCCESS")
            results["go"] = "PASS"
        else:
            print(f"Go Integration: FAILED (Trace data: {trace_data})")
            results["go"] = "FAIL"

    finally:
        print("\n=== Cleaning up traceserver container ===")
        subprocess.run("docker rm -f traceserver-integration-test 2>/dev/null", shell=True)
        # Cleanup test files
        subprocess.run("rm -f /tmp/py_test.py", shell=True)
        subprocess.run(f"rm -f {node_dir}/node_test.cjs", shell=True)
        subprocess.run(f"rm -rf {go_dir}/tests/integration/go_test", shell=True)
        
    print("\n=== INTEGRATION TEST SUMMARY ===")
    for lang, status in results.items():
        print(f"{lang.upper()}: {status}")
        
    if "FAIL" in results.values() or not results:
        print("Integration tests FAILED!")
        sys.exit(1)
    else:
        print("All integration tests PASSED!")
        sys.exit(0)

if __name__ == "__main__":
    main()
