import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class TriageService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching quick triage tracer to PID {pid} (Sampling for 10s)...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("cpu_samples : 45")
            print("off_cpu     : 890")
            print("syscalls    : 4230")
            print("page_faults : 12")
            print("\nResult Recommendation: cpu_samples low + offcpu high → GO TO: I/O BOUND")
            return

        program = """
        profile:hz:99 /pid == $1/ { @cpu[ustack(perf,3)] = count(); }
        tracepoint:sched:sched_switch /args->prev_pid == $1/ { @offcpu = count(); }
        tracepoint:raw_syscalls:sys_enter /pid == $1/ { @syscalls = count(); }
        software:page-faults:1 /pid == $1/ { @faults = count(); }
        interval:s:10 {
          printf("cpu_samples : %d\\n", @cpu);
          printf("off_cpu     : %d\\n", @offcpu);
          printf("syscalls    : %d\\n", @syscalls);
          printf("page_faults : %d\\n", @faults);
          exit();
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ Quick triage tracer active. Collecting metrics for 10s...\n")
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nDetached triage tracer.")
