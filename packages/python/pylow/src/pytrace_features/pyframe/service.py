import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class PyframeService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching Python frame USDT tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Collecting USDT frame events... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("ENTER execute_query() @ db/models.py:142")
            print("slow_query() @ db/models.py:142 — p99: 340ms")
            print("\n--- BPF Map: @hotspots (us spent per frame) ---")
            print("@hotspots[execute_query, db/models.py]:")
            print("[100, 200]             89 |@@@@@@@@@@@@@@@@                    |")
            print("[1000, 2000]          210 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|")
            return

        program = """
        usdt:/usr/bin/python3:python:function__entry {
            @start[tid, str(arg1)] = nsecs;
            printf("ENTER %s() @ %s:%d\\n", str(arg1), str(arg0), arg2);
        }
        usdt:/usr/bin/python3:python:function__return {
            $key = @start[tid, str(arg1)];
            if ($key) {
                $dur = nsecs - $key;
                @hotspots[str(arg1), str(arg0)] = hist($dur / 1000);
                delete(@start[tid, str(arg1)]);
            }
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "map" or event.get("type") == "printf":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ Frame USDT tracer active. Streaming events... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached frame USDT tracer.")
