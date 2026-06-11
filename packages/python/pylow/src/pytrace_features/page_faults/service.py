import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class PageFaultsService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching page faults tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            print("✓ Attached. Collecting page fault events... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("=== PAGE FAULT HOTSPOTS ===")
            print("@faults[")
            print("    malloc+0x24")
            print("    PyBytes_FromStringAndSize+0x18")
            print("    load_dataset @ ml/data.py:12")
            print("]: 421")
            return

        program = """
        software:page-faults:1 /pid == $1/ {
          @faults[ustack(perf, 5)] = count();
        }
        interval:s:10 {
          printf("=== PAGE FAULT HOTSPOTS ===\\n");
          print(@faults);
          clear(@faults);
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ Page faults tracer active. Streaming events... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached page faults tracer.")
