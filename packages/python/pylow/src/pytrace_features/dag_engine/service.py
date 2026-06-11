"""
DAG Execution Engine service.

Topological-sort (Kahn's algorithm) based parallel step executor.
Usage: pylow dag-run --dag auth:,get_user:auth,get_catalog:auth,create_order:get_user,get_catalog
       pylow dag-run --dag-file /path/to/dag.json
       pylow dag-dry-run --dag auth:,get_user:auth
       pylow dag-status
"""
import sys
import json
import time
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Optional
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

_COLORS = {
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "CYAN": "\033[96m",
    "BOLD": "\033[1m",
    "RESET": "\033[0m",
}

def _c(color: str, text: str) -> str:
    return f"{_COLORS.get(color, '')}{text}{_COLORS['RESET']}"


def _parse_dag_spec(spec: str) -> Dict[str, List[str]]:
    """Parse 'step:dep1,dep2 step2:dep1' into {step: [deps]}."""
    dag: Dict[str, List[str]] = {}
    for token in spec.split():
        if ":" in token:
            step, deps_raw = token.split(":", 1)
            deps = [d for d in deps_raw.split(",") if d]
        else:
            step, deps = token, []
        dag[step] = deps
    return dag


def _topological_levels(dag: Dict[str, List[str]]) -> Optional[List[List[str]]]:
    """
    Kahn's algorithm. Returns levels (each level can run in parallel).
    Returns None if a cycle is detected.
    """
    in_degree: Dict[str, int] = {n: 0 for n in dag}
    reverse: Dict[str, List[str]] = {n: [] for n in dag}
    for node, deps in dag.items():
        for d in deps:
            if d not in dag:
                dag[d] = []
                in_degree[d] = 0
                reverse[d] = []
            in_degree[node] += 1
            reverse[d].append(node)

    queue = deque([n for n, deg in in_degree.items() if deg == 0])
    levels: List[List[str]] = []
    visited = 0

    while queue:
        level = list(queue)
        levels.append(level)
        queue.clear()
        for node in level:
            visited += 1
            for child in reverse[node]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

    if visited != len(dag):
        return None  # cycle
    return levels


class DagEngineService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()
        self._status: Dict[str, str] = {}
        self._lock = threading.Lock()

    def run(self, dag_spec: str, dag_file: str | None, dry: bool, max_workers: int) -> None:
        # Load DAG
        if dag_file:
            try:
                with open(dag_file) as f:
                    raw = json.load(f)
                dag = {k: (v if isinstance(v, list) else v.split(",")) for k, v in raw.items()}
            except Exception as e:
                print(_c("RED", f"[dag-engine] Cannot load dag-file: {e}"), file=sys.stderr)
                sys.exit(1)
        else:
            dag = _parse_dag_spec(dag_spec)

        if not dag:
            print(_c("RED", "[dag-engine] Empty DAG — nothing to run."), file=sys.stderr)
            sys.exit(1)

        levels = _topological_levels(dag)
        if levels is None:
            print(_c("RED", "[dag-engine] CYCLE DETECTED — aborting."), file=sys.stderr)
            sys.exit(1)

        print(_c("BOLD", "\n=== DAG EXECUTION ENGINE ==="))
        print(f"  Steps     : {len(dag)}")
        print(f"  Levels    : {len(levels)}")
        print(f"  Workers   : {max_workers}")
        print(f"  Mode      : {'DRY RUN' if dry else 'EXECUTE'}\n")

        for i, level in enumerate(levels):
            print(_c("CYAN", f"  Level {i}  [{', '.join(level)}]"))
        print()

        if dry:
            print(_c("GREEN", "✓ DAG is valid. No cycles. Dry-run complete."))
            return

        total_start = time.monotonic()
        failed: List[str] = []

        for i, level in enumerate(levels):
            print(_c("YELLOW", f"\n▶ Level {i}: {level}"))
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {pool.submit(self._exec_step, step): step for step in level}
                for fut in as_completed(futures):
                    step = futures[fut]
                    ok, dur = fut.result()
                    symbol = _c("GREEN", "✓") if ok else _c("RED", "✗")
                    print(f"  {symbol} {step:20s} {dur*1000:.1f}ms")
                    if not ok:
                        failed.append(step)

            if failed:
                print(_c("RED", f"\n[dag-engine] FAILED at level {i}: {failed}"))
                sys.exit(1)

        elapsed = time.monotonic() - total_start
        print(_c("GREEN", f"\n✓ All {len(dag)} steps completed in {elapsed*1000:.1f}ms"))

    def _exec_step(self, step: str):
        start = time.monotonic()
        with self._lock:
            self._status[step] = "RUNNING"
        # Simulate or call the actual step
        try:
            time.sleep(0.05)  # placeholder — replace with real dispatch
            with self._lock:
                self._status[step] = "DONE"
            return True, time.monotonic() - start
        except Exception as e:
            with self._lock:
                self._status[step] = f"FAILED: {e}"
            return False, time.monotonic() - start

    def status(self) -> None:
        if not self._status:
            print("No DAG run in progress.")
            return
        print(_c("BOLD", "=== DAG STATUS ==="))
        for step, st in self._status.items():
            color = "GREEN" if st == "DONE" else "RED" if "FAIL" in st else "YELLOW"
            print(f"  {_c(color, st):30s}  {step}")
