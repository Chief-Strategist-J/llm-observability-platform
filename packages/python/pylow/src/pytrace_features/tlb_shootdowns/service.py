import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class TlbShootdownsService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching TLB shootdowns tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            print("✓ Attached. Monitoring TLB flushes... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("\n--- BPF Map: @tlb_reason ---")
            print("[0] (TLB_FLUSH_ON_TASK_SWITCH)              42")
            print("[1] (TLB_FLUSH_ON_PAGE_FAULT)              187")
            return

        program = """
        tracepoint:tlb:tlb_flush /pid == $1/ {
          @tlb_flushes = count();
          @tlb_reason[args->reason] = count();
        }
        interval:s:5 { print(@tlb_reason); clear(@tlb_reason); }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ TLB shootdowns tracer active. Streaming events... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached TLB shootdowns tracer.")
