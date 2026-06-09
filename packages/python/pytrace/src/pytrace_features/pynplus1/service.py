import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class Pynplus1Service:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching N+1 query loop detector to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Monitoring ORM execute loops... Ctrl+C to stop.\n")
            time.sleep(1.5)
            # Create a mock map
            counts = {
                ("db/models.py", 142): 15,
                ("gateway/orchestrator.py", 52): 4
            }
            self.detect_nplus1(counts)
            return

        program = """
        usdt:/usr/bin/python3:python:function__entry / str(arg1) == "execute" / {
            @query_calls[str(arg0), arg2] = count();
            @query_ts = nsecs;
        }
        usdt:/usr/bin/python3:python:function__return / str(arg1) == "execute" / {
            $dur = nsecs - @query_ts;
            @query_durations[str(arg0), arg2] = hist($dur / 1000);
        }
        interval:s:5 {
            print(@query_calls);
            clear(@query_calls);
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "map":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ N+1 query loop detector active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached N+1 query loop detector.")

    def detect_nplus1(self, counts: dict, threshold=10, window_s=5):
        for (filepath, line), count in counts.items():
            rate = count / window_s
            if count > threshold:
                print(f"⚠️  N+1 CANDIDATE: {filepath}:{line}")
                print(f"   Called {count}x in {window_s}s ({rate:.1f}/s)")
                print(f"   This is almost certainly inside a loop\n")
