#!/usr/bin/env python3
import os
import sys
import time

# Ensure we can import pytrace modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from pytrace_infra.adapters.sqlite_store import SQLiteStore
from pytrace_features.flow.service import FlowService
from pytrace_features.stitch.service import StitchService
from pytrace_features.slow.service import SlowService
from pytrace_features.diff.service import DiffService

# Import all 26 services
from pytrace_features.syscall.service import SyscallService
from pytrace_features.malloc.service import MallocService
from pytrace_features.tcp.service import TcpService
from pytrace_features.io.service import IoService
from pytrace_features.flame.service import FlameService
from pytrace_features.sched.service import SchedService
from pytrace_features.pycall.service import PycallService
from pytrace_features.pyframe.service import PyframeService
from pytrace_features.pycpu.service import PycpuService
from pytrace_features.pyexcept.service import PyexceptService
from pytrace_features.pyiowait.service import PyiowaitService
from pytrace_features.pygil.service import PygilService
from pytrace_features.pyleak.service import PyleakService
from pytrace_features.pyreq.service import PyreqService
from pytrace_features.timeline.service import TimelineService
from pytrace_features.pythread.service import PythreadService
from pytrace_features.pyasync.service import PyasyncService
from pytrace_features.pyargs.service import PyargsService
from pytrace_features.pysyscall.service import PysyscallService
from pytrace_features.pynplus1.service import Pynplus1Service
from pytrace_features.pygraph.service import PygraphService
from pytrace_features.pyanomaly.service import PyanomalyService
from pytrace_features.pydash.service import PydashService
from pytrace_features.pysingle.service import PysingleService

def run_all_features_demo():
    print("=" * 80)
    # Clear and clean DB for demo
    db_path = "pytrace.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    store = SQLiteStore(db_path)
    
    # Seeding database
    trace_id = "t_demo_123"
    now_ns = int(time.time() * 1e9)
    store.insert_trace(trace_id, now_ns, now_ns + 500_000_000)
    store.insert_event(trace_id, "usdt_entry", 1, now_ns, "handle_request", 500_000_000, "api")
    store.insert_event(trace_id, "usdt_entry", 1, now_ns + 10_000_000, "validate_token", 50_000_000, "api")
    store.insert_event(trace_id, "usdt_entry", 1, now_ns + 100_000_000, "execute_query", 350_000_000, "api")

    # 1. Flow Service
    print("\n--- 1. FLOW RENDERER ---")
    flow = FlowService(store)
    flow.render_tree([])

    # 2. Stitch Service
    print("\n--- 2. DISTRIBUTED TRACE STITCHING ---")
    stitch = StitchService(store)
    stitch.stitch_traces(["api"])

    # 3. Slow Path Monitor
    print("\n--- 3. SLOW PATH MONITOR ---")
    slow = SlowService(store)
    slow.monitor(threshold_ms=100, watch=False)

    # 4. Diff Service
    print("\n--- 4. COMPARE / DIFF SERVICE ---")
    diff = DiffService(store)
    diff.compare("v1.2", "v1.3")

    # List of all bpf features
    features = [
        ("SYSCALL COUNTS & LATENCY (syscall)", SyscallService()),
        ("MEMORY ALLOCATION PROFILE (malloc)", MallocService()),
        ("TCP SEND LATENCY (tcp)", TcpService()),
        ("FILE I/O LATENCY (io)", IoService()),
        ("SCHEDULER RUNQUEUE LATENCY (sched)", SchedService()),
        ("PYTHON FUNCTION TIMER (pycall)", PycallService()),
        ("PYTHON EXACT FRAMES (pyframe)", PyframeService()),
        ("PYTHON CPU HOTSPOTS (pycpu)", PycpuService()),
        ("PYTHON EXCEPTIONS (pyexcept)", PyexceptService()),
        ("PYTHON BLOCKING I/O WAITS (pyiowait)", PyiowaitService()),
        ("PYTHON GIL CONTENTION (pygil)", PygilService()),
        ("MEMORY LEAK DETECTION (pyleak)", PyleakService()),
        ("REQUEST LIFECYCLE BREAKDOWN (pyreq)", PyreqService()),
        ("THREAD-AWARE TIMELINE (pythread)", PythreadService()),
        ("ASYNC COROUTINE METRICS (pyasync)", PyasyncService()),
        ("FUNCTION ARGUMENT LAYOUT (pyargs)", PyargsService()),
        ("PYTHON ATTRIBUTED SYSCALLS (pysyscall)", PysyscallService()),
        ("ORM N+1 QUERY DETECTION (pynplus1)", Pynplus1Service()),
        ("CALL GRAPH RELATIONSHIPS (pygraph)", PygraphService()),
        ("ANOMALY DETECTION (pyanomaly)", PyanomalyService()),
        ("CURSES LIVE DASHBOARD (pydash)", PydashService()),
    ]

    for i, (name, service) in enumerate(features, start=5):
        print(f"\n--- {i}. {name} ---")
        try:
            service.trace(1234)
        except Exception as e:
            print(f"Error executing feature: {e}")

    # Special / Multi-argument services
    print("\n--- 26. FLAME GRAPH SAMPLER (flame) ---")
    FlameService().trace(1234, duration_s=1)

    print("\n--- 27. CHRONOLOGICAL TIMELINE (timeline) ---")
    TimelineService().trace(1234, duration_s=1.0)

    print("\n--- 28. SINGLE EXECUTION TRACER (pysingle) ---")
    PysingleService().trace(1234, "handle_request")

if __name__ == "__main__":
    run_all_features_demo()
