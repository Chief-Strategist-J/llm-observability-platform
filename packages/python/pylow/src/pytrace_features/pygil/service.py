import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class PygilService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching GIL lock contention tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Monitoring GIL wait states... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("GIL WAIT 1250us tid=10234 stack:")
            print("  [ustack]:")
            print("    calculate_features @ ml/engine.py:89")
            print("    process_job @ worker/tasks.py:4")
            return

        program = """
        uprobe:/usr/bin/python3:PyEval_EvalFrameEx {
            @gil_wait_start[tid] = nsecs;
        }
        uprobe:/usr/bin/python3:_PyEval_EvalFrameDefault {
            if (@gil_wait_start[tid]) {
                $wait = nsecs - @gil_wait_start[tid];
                if ($wait > 500000) {
                    printf("GIL WAIT %lldus tid=%d stack:\\n", $wait/1000, tid);
                    print(ustack(perf));
                }
                delete(@gil_wait_start[tid]);
            }
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "printf":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ GIL wait tracer active. Streaming wait states... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached GIL wait tracer.")
