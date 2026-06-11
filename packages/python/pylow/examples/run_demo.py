#!/usr/bin/env python3
import os
import sys
import time

# Ensure we can import pytrace modules by adding src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from pytrace_infra.adapters.sqlite_store import SQLiteStore
from pytrace_features.flow.service import FlowService
from pytrace_features.stitch.service import StitchService
from pytrace_features.slow.service import SlowService
from pytrace_features.diff.service import DiffService

def clean_database():
    """Start fresh by cleaning any old pytrace.db database."""
    db_path = "pytrace.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    print("✓ Cleaned existing pytrace.db")

def simulate_real_traces(store: SQLiteStore):
    """Seed the database with real execution trace logs (no spans)."""
    trace_id = "t_demo_flow_123"
    now_ns = int(time.time() * 1e9)
    
    store.insert_trace(trace_id, now_ns, now_ns + 450_000_000)
    
    # Insert events only (no spans table insertions)
    store.insert_event(trace_id, "usdt_entry", 1, now_ns, "handle_request", 450_000_000, "api-gateway")
    store.insert_event(trace_id, "usdt_entry", 1, now_ns + 5_000_000, "authenticate_user", 20_000_000, "api-gateway")
    store.insert_event(trace_id, "db_query", 1, now_ns + 7_000_000, "redis GET session_id", 15_000_000, "api-gateway")
    store.insert_event(trace_id, "usdt_entry", 1, now_ns + 30_000_000, "call_llm_chain", 410_000_000, "api-gateway")
    store.insert_event(trace_id, "http_outbound", 1, now_ns + 35_000_000, "POST api.openai.com/v1/chat/completions", 400_000_000, "api-gateway")
    store.insert_event(trace_id, "syscall_wait", 1, now_ns + 40_000_000, "waiting (epoll_wait)", 390_000_000, "api-gateway")

def run_tests():
    clean_database()
    store = SQLiteStore("pytrace.db")
    simulate_real_traces(store)

    print("\n" + "="*50)
    print("1. RUNNING FLOW RENDERER (FROM DB EVENTS - NO SPANS)")
    print("="*50)
    flow = FlowService(store)
    flow.render_tree([])

    print("\n" + "="*50)
    print("2. RUNNING FLOW RENDERER (FROM EVENTS LIST PARAMETER - NO DATABASE)")
    print("="*50)
    empty_store = SQLiteStore(":memory:")
    now = time.time()
    raw_events = [
        {"timestamp": now - 0.500, "name": "handle_request", "duration_ms": 500.0},
        {"timestamp": now - 0.480, "name": "authenticate", "duration_ms": 50.0},
        {"timestamp": now - 0.470, "name": "redis_get", "duration_ms": 30.0},
        {"timestamp": now - 0.290, "name": "call_llm_model", "duration_ms": 280.0},
        {"timestamp": now - 0.280, "name": "POST api.openai.com", "duration_ms": 270.0},
        {"timestamp": now - 0.270, "name": "waiting (epoll_wait)", "duration_ms": 250.0}
    ]
    flow_ev = FlowService(empty_store)
    flow_ev.render_tree(raw_events)

    print("\n" + "="*50)
    print("3. RUNNING DISTRIBUTED TRACE STITCHING")
    print("="*50)
    stitch = StitchService(store)
    stitch.stitch_traces(["api-gateway"])

    print("\n" + "="*50)
    print("4. RUNNING SLOW PATH MONITOR (Threshold: 200ms)")
    print("="*50)
    slow = SlowService(store)
    slow.monitor(threshold_ms=200, watch=False)

    print("\n" + "="*50)
    print("5. RUNNING COMPARE/DIFF SERVICE (v1.2 vs v1.3)")
    print("="*50)
    diff = DiffService(store)
    diff.compare("v1.2", "v1.3")

    print("\n" + "="*50)
    print("6. RUNNING SINGLE EXECUTION TRACER (pysingle)")
    print("="*50)
    from pytrace_features.pysingle.service import PysingleService
    single = PysingleService(store)
    single.trace(1234, "handle_request")

if __name__ == "__main__":
    run_tests()
