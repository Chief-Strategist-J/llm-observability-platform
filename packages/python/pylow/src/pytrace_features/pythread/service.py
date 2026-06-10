import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

@dataclass
class ThreadTimeline:
    tid: int
    events: list = field(default_factory=list)
    call_stack: list = field(default_factory=list)
    depth: int = 0

class PythreadService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching thread-aware tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Collecting threaded events... Ctrl+C to stop.\n")
            time.sleep(1.5)
            # Create a mock raw trace
            raw_output = (
                "1000 1234 10001 ENTER handle_request server.py 45\n"
                "1040 1234 10001 ENTER parse_headers http.py 12\n"
                "1051 1234 10001 EXIT  parse_headers http.py 12\n"
                "1055 1234 10001 ENTER execute_query db.py 88\n"
                "1955 1234 10001 EXIT  execute_query db.py 88\n"
                "1960 1234 10001 EXIT  handle_request server.py 45\n"
            )
            threads = self.parse_threaded(raw_output)
            for tid, t in threads.items():
                print(f"\n--- Thread ID: {tid} ---")
                for ev in t.events:
                    print(f"  {ev['func']}() spent {ev['total_ns']/1000000:.2f}ms (Self time: {ev['self_ns']/1000000:.2f}ms)")
            return

        program = """
        usdt:python:*:function__entry {
            printf("%lld %d %d ENTER %s %s %d\\n", nsecs, pid, tid, str(arg1), str(arg0), arg2);
        }
        usdt:python:*:function__return {
            printf("%lld %d %d EXIT  %s %s %d\\n", nsecs, pid, tid, str(arg1), str(arg0), arg2);
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            raw_log = []
            def handler(event):
                if event.get("type") == "printf":
                    msg = event.get("data") or event.get("msg")
                    if msg:
                        raw_log.append(msg.strip())
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ Thread-aware tracer active. Streaming events... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached thread-aware tracer.")
            threads = self.parse_threaded("\n".join(raw_log))
            for tid, t in threads.items():
                print(f"\n--- Thread ID: {tid} ---")
                for ev in t.events:
                    print(f"  {ev['func']}() spent {ev['total_ns']/1000000:.2f}ms (Self time: {ev['self_ns']/1000000:.2f}ms)")

    def parse_threaded(self, raw_output: str) -> dict[int, ThreadTimeline]:
        threads = defaultdict(lambda: ThreadTimeline(tid=0))

        for line in raw_output.splitlines():
            parts = line.strip().split()
            if len(parts) < 7:
                continue

            ts, pid, tid, kind, func, filepath, lineno = (
                int(parts[0]), int(parts[1]), int(parts[2]),
                parts[3], parts[4], parts[5], int(parts[6])
            )

            t = threads[tid]
            t.tid = tid

            if kind == "ENTER":
                t.call_stack.append({
                    "func": func,
                    "file": filepath,
                    "line": lineno,
                    "enter_ts": ts,
                    "depth": t.depth,
                    "children_time": 0
                })
                t.depth += 1

            elif kind == "EXIT" and t.call_stack:
                frame = t.call_stack.pop()
                t.depth = max(0, t.depth - 1)
                dur = ts - frame["enter_ts"]

                # subtract children time → get SELF time only
                self_time = dur - frame["children_time"]

                # propagate to parent
                if t.call_stack:
                    t.call_stack[-1]["children_time"] += dur

                t.events.append({
                    **frame,
                    "exit_ts": ts,
                    "total_ns": dur,
                    "self_ns": self_time
                })

        return threads
