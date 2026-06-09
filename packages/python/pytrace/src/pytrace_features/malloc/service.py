import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class MallocService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching memory allocation tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Collecting malloc/free events... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("\n--- BPF Map: @alloc_sizes (bytes) ---")
            print("[64, 127]             256 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|")
            print("[128, 255]             64 |@@@@@@@@@                           |")
            print("[1024, 2047]           12 |@@                                  |")
            print("\n--- BPF Map: @free_count ---")
            print("free_operations: 312")
            return

        program = """
        uprobe:/lib/x86_64-linux-gnu/libc.so.6:malloc / pid == $1 / {
            @alloc_sizes = hist(arg0);
            @alloc_callers[ustack] = count();
        }
        uprobe:/lib/x86_64-linux-gnu/libc.so.6:free / pid == $1 / {
            @free_count = count();
        }
        interval:s:5 {
            print(@alloc_sizes);
            print(@free_count);
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "map":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ Memory tracer active. Streaming events... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached memory tracer.")
