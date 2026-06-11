"""
Saga Orchestrator service.

Forward/compensate step pattern with saga log, rollback on failure.
Usage: pylow saga-run --steps auth,create_order,reserve_inventory,create_payment
       pylow saga-run --steps auth,create_order --fail-at create_order
       pylow saga-log [--log-file /tmp/saga.log]
       pylow saga-replay --log-file /tmp/saga.log
"""
import sys
import json
import time
import datetime
import os
from typing import List, Dict, Optional
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

_DEFAULT_LOG = "/tmp/pylow_saga.log"

_COLORS = {
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "CYAN": "\033[96m",
    "MAGENTA": "\033[95m",
    "BOLD": "\033[1m",
    "RESET": "\033[0m",
}

def _c(color: str, text: str) -> str:
    return f"{_COLORS.get(color, '')}{text}{_COLORS['RESET']}"


class SagaOrchestrator:
    """
    Runs forward steps in order.
    On failure: runs compensating transactions in reverse order for all completed steps.
    Appends every event to a saga log file (JSON Lines).
    """

    def __init__(self, log_file: str = _DEFAULT_LOG) -> None:
        self.log_file = log_file
        self.completed: List[str] = []
        self.saga_id = f"saga-{int(time.time())}"

    def _log(self, event: str, step: str, detail: str = "") -> None:
        entry = {
            "saga_id": self.saga_id,
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
            "event": event,
            "step": step,
            "detail": detail,
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _execute_step(self, step: str, fail_at: str | None) -> bool:
        """Simulate step execution. Returns True on success."""
        self._log("FORWARD_START", step)
        time.sleep(0.04)
        if fail_at and step == fail_at:
            self._log("FORWARD_FAIL", step, "injected failure")
            return False
        self._log("FORWARD_OK", step)
        return True

    def _compensate_step(self, step: str) -> None:
        """Simulate compensating transaction."""
        self._log("COMPENSATE_START", step)
        time.sleep(0.02)
        self._log("COMPENSATE_OK", step)

    def run(self, steps: List[str], fail_at: str | None = None) -> None:
        print(_c("BOLD", f"\n=== SAGA ORCHESTRATOR [{self.saga_id}] ==="))
        print(f"  Steps    : {', '.join(steps)}")
        print(f"  Log file : {self.log_file}")
        print(f"  Inject   : {fail_at or 'none'}\n")

        self._log("SAGA_START", "", f"steps={steps}")

        for step in steps:
            print(f"  {_c('CYAN', '▶')} Forward  {step}", end="  ", flush=True)
            ok = self._execute_step(step, fail_at)
            if ok:
                self.completed.append(step)
                print(_c("GREEN", "✓"))
            else:
                print(_c("RED", "✗  FAILED"))
                print(_c("YELLOW", "\n  Rolling back completed steps..."))
                for done_step in reversed(self.completed):
                    print(f"  {_c('MAGENTA', '↩')} Compensate {done_step}", end="  ", flush=True)
                    self._compensate_step(done_step)
                    print(_c("GREEN", "✓"))
                self._log("SAGA_ROLLED_BACK", step)
                print(_c("RED", f"\n✗ Saga rolled back. Failed at: {step}"))
                print(f"  Log: {self.log_file}")
                return

        self._log("SAGA_COMMITTED", "", f"all_steps={steps}")
        print(_c("GREEN", f"\n✓ Saga committed. All {len(steps)} steps succeeded."))
        print(f"  Log: {self.log_file}")


class SagaOrchestratorService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, steps_raw: str, fail_at: str | None, log_file: str) -> None:
        steps = [s.strip() for s in steps_raw.split(",") if s.strip()]
        if not steps:
            print(_c("RED", "[saga] No steps provided."), file=sys.stderr)
            sys.exit(1)
        saga = SagaOrchestrator(log_file=log_file)
        saga.run(steps, fail_at=fail_at)

    def show_log(self, log_file: str) -> None:
        if not os.path.exists(log_file):
            print(f"[saga-log] No log at {log_file}")
            return
        print(_c("BOLD", f"=== SAGA LOG: {log_file} ===\n"))
        event_colors = {
            "SAGA_START": "CYAN",
            "FORWARD_START": "YELLOW",
            "FORWARD_OK": "GREEN",
            "FORWARD_FAIL": "RED",
            "COMPENSATE_START": "MAGENTA",
            "COMPENSATE_OK": "GREEN",
            "SAGA_ROLLED_BACK": "RED",
            "SAGA_COMMITTED": "GREEN",
        }
        with open(log_file) as f:
            for line in f:
                try:
                    e = json.loads(line)
                    col = event_colors.get(e["event"], "RESET")
                    step_label = f" [{e['step']}]" if e["step"] else ""
                    detail = f" — {e['detail']}" if e.get("detail") else ""
                    print(f"  {e['ts']}  {_c(col, e['event']):40s}{step_label}{detail}")
                except Exception:
                    print(line.rstrip())

    def replay(self, log_file: str) -> None:
        """Re-run the steps from a committed saga log (forward only, no injected failures)."""
        if not os.path.exists(log_file):
            print(f"[saga-replay] No log at {log_file}")
            return
        steps = []
        with open(log_file) as f:
            for line in f:
                try:
                    e = json.loads(line)
                    if e["event"] == "SAGA_START":
                        # parse steps from detail
                        raw = e.get("detail", "")
                        if raw.startswith("steps="):
                            import ast
                            steps = ast.literal_eval(raw[len("steps="):])
                except Exception:
                    pass
        if not steps:
            print("[saga-replay] Could not extract steps from log.")
            return
        print(_c("CYAN", f"[saga-replay] Replaying {len(steps)} steps from {log_file}"))
        saga = SagaOrchestrator(log_file=log_file + ".replay")
        saga.run(steps, fail_at=None)
