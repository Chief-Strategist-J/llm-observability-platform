#!/usr/bin/env python3
import os
import sys
import time

# Ensure we can import pytrace modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from pytrace_features.pysingle.service import PysingleService

def show_self_time_rule_examples():
    print("=" * 80)
    print("DEMONSTRATING THE SELF TIME RULE AND DIAGNOSTIC SCENARIOS")
    print("=" * 80)
    
    print("\n[SCENARIO 1] Self Time ≈ Total Time (Leaf Node Bottleneck)")
    print("Description: A leaf node function has high self time and high total time. It has no children,")
    print("so the execution time is spent entirely within its own logic (e.g. database query, CPU work).")
    print("-" * 80)
    
    # Simulating a leaf node bottleneck
    now_ns = int(time.time() * 1e9)
    events_scenario_1 = [
        {"ts": now_ns, "tid": 20001, "kind": "ENTER", "func": "execute_query", "file": "db.py", "line": 102},
        {"ts": now_ns + 120_000_000, "tid": 20001, "kind": "EXIT", "func": "execute_query", "file": "db.py", "line": 102}
    ]
    service = PysingleService()
    service.render(events_scenario_1)

    print("\n[SCENARIO 2] Self Time Low, Total Time High (Intermediary/Caller Node)")
    print("Description: An intermediary function has high total time but very low self time.")
    print("This means the function itself is fast, but it is waiting on a slow child function.")
    print("-" * 80)
    
    events_scenario_2 = [
        {"ts": now_ns, "tid": 20002, "kind": "ENTER", "func": "get_user", "file": "db.py", "line": 88},
        {"ts": now_ns + 1_000_000, "tid": 20002, "kind": "ENTER", "func": "execute_query", "file": "db.py", "line": 102},
        {"ts": now_ns + 121_000_000, "tid": 20002, "kind": "EXIT", "func": "execute_query", "file": "db.py", "line": 102},
        {"ts": now_ns + 122_000_000, "tid": 20002, "kind": "EXIT", "func": "get_user", "file": "db.py", "line": 88}
    ]
    service.render(events_scenario_2)

    print("\n[SCENARIO 3] Self Time High in Non-Leaf Node (Heavy Computation + Child Calls)")
    print("Description: A function has child calls, but its self time is also high.")
    print("This indicates that the function itself performs heavy CPU work or blocking operations")
    print("in addition to calling other services/functions.")
    print("-" * 80)
    
    events_scenario_3 = [
        {"ts": now_ns, "tid": 20003, "kind": "ENTER", "func": "process_data", "file": "analyzer.py", "line": 10},
        # child call that finishes quickly
        {"ts": now_ns + 5_000_000, "tid": 20003, "kind": "ENTER", "func": "load_config", "file": "config.py", "line": 5},
        {"ts": now_ns + 10_000_000, "tid": 20003, "kind": "EXIT", "func": "load_config", "file": "config.py", "line": 5},
        # heavy loop inside process_data (150ms of self work before next event/exit)
        {"ts": now_ns + 160_000_000, "tid": 20003, "kind": "EXIT", "func": "process_data", "file": "analyzer.py", "line": 10}
    ]
    service.render(events_scenario_3)

if __name__ == "__main__":
    show_self_time_rule_examples()
