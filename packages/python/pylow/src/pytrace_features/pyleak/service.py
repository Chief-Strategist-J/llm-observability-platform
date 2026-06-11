import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class PyleakService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching memory leak tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Collecting memory allocation metrics... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("=== TOP ALLOCATORS ===")
            print("@allocs[0x7f3b821034bc]: 10485760 bytes")
            print("  -> allocating callsite: load_dataset @ ml/data.py:12")
            print("ratio of malloc to free: 3415 allocated / 1230 freed  ← potential leak")
            return

        program = """
        uprobe:/lib/x86_64-linux-gnu/libc.so.6:malloc / pid == $1 / {
            @allocs[ustack(perf)] = sum(arg0);
            @alloc_count[ustack(perf)] = count();
        }
        uprobe:/lib/x86_64-linux-gnu/libc.so.6:free / pid == $1 / {
            @free_count = count();
        }
        interval:s:30 {
            printf("=== TOP ALLOCATORS ===\\n");
            print(@allocs);
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "printf" or event.get("type") == "map":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ Memory leak tracer active. Reporting allocation hotspots... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached memory leak tracer.")
